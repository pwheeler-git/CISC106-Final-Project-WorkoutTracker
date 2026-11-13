'''Track exercises with Drafter.'''

from dataclasses import dataclass
from drafter import *

MUSCLE_GROUPS = ("Chest", "Back", "Legs", "Shoulders", "Arms", "Core", "Other")


@dataclass
class WorkoutEntry:
    '''Store one exercise entry.'''

    exercise_name: str
    muscle_group: str
    sets: int
    reps: int
    weight: float


@dataclass
class State:
    '''Store the workout log and settings.'''

    entries: list[WorkoutEntry]
    name: str
    set_goal: int
    selected_muscle_group: str


def total_sets(entries: list[WorkoutEntry]) -> int:
    '''Add up all sets.'''
    result = 0
    for entry in entries:
        result += entry.sets
    return result


def total_volume(entries: list[WorkoutEntry]) -> float:
    '''Add up sets times reps times weight.'''
    result = 0.0
    for entry in entries:
        result += entry.sets * entry.reps * entry.weight
    return result


def metric(label: str, value: str) -> Div:
    '''Show a label and total.'''
    return Div([
        Paragraph(label),
        Paragraph(value),
    ])


def goal_card(state: State) -> Div:
    '''Show progress toward the set goal.'''
    completed = total_sets(state.entries)
    remaining = state.set_goal - completed
    if remaining <= 0:
        message = "Goal reached! Every set added up."
    else:
        message = str(remaining) + " more sets to reach your goal."
    return Div([
        Paragraph("YOUR TOTAL-SET GOAL"),
        Header(str(completed) + " / " + str(state.set_goal) + " sets", level=2),
        ProgressBar(min(completed, state.set_goal), state.set_goal),
        Paragraph(message),
    ])

 
def site_page(state: State, content: list) -> Page:
    '''Add navigation buttons to a page.'''
    return Page(state, [
        Header("LiftLog"),
        Button("Home", index),
        Button("Log Exercise", log_exercise),
        Button("History", history),
        Button("Statistics", statistics),
        Button("Settings", settings),
        Div(content),
        Paragraph("This visit only: refreshing or closing the page starts a new log."),
    ])


@route
def index(state: State) -> Page:
    '''Show the home page.'''
    content = [
        Paragraph("YOUR TRAINING JOURNAL"),
        Header("Welcome, " + state.name + "!"),
        Paragraph("Small steps. Stronger habits. Keep a record of the work you put in."),
        Div([
            Button("+ Log Exercise", log_exercise),
            Button("View History", history),
        ]),
        Div([
            metric("Exercises logged", str(len(state.entries))),
            metric("Sets completed", str(total_sets(state.entries))),
            metric("Lifting volume", f"{total_volume(state.entries):,.1f} lb"),
        ]),
        goal_card(state),
    ]
    if not state.entries:
        content.append(Div([
            Header("Your next chapter starts with one set.", level=2),
            Paragraph("Log an exercise to start your history and see your totals grow."),
        ]))
    else:
        latest = state.entries[-1]
        content.append(Div([
            Paragraph("LAST EXERCISE LOGGED"),
            Header(latest.exercise_name, level=2),
            Paragraph(entry_summary(latest)),
        ]))
    return site_page(state, content)


def entry_summary(entry: WorkoutEntry) -> str:
    '''Return the exercise details as text.'''
    return (entry.muscle_group + " · " + str(entry.sets) + " sets × "
            + str(entry.reps) + " reps × " + f"{entry.weight:g} lb")


def exercise_form(state: State, error: str = "", exercise_name: str = "",
                  muscle_group: str = "Chest", sets: str = "3",
                  reps: str = "10", weight: str = "0") -> Page:
    '''Show exercise inputs and any error.'''
    content = [
        Paragraph("PUT IN THE WORK"),
        Header("Log an exercise"),
        Paragraph("Record sets performed with the same reps and weight."),
    ]
    if error:
        content.append(Paragraph(error, role="alert"))
    content.append(Div([
        Div([Label("Exercise name", "exercise_name"),
             TextBox("exercise_name", exercise_name, placeholder="e.g. Bench Press",
                     maxlength=60)]),
        Div([Label("Muscle group", "muscle_group"),
             SelectBox("muscle_group", list(MUSCLE_GROUPS), muscle_group)]),
        Div([
            Div([Label("Sets", "sets"), TextBox("sets", sets)]),
            Div([Label("Reps per set", "reps"), TextBox("reps", reps)]),
            Div([Label("Weight (lb)", "weight"), TextBox("weight", weight)]),
        ]),
        Paragraph("Use whole numbers for sets and reps. Enter 0 lb for unweighted exercises."),
        Div([Button("Save Exercise", save_exercise),
             Button("Home", index)]),
    ]))
    return site_page(state, content)


@route
def log_exercise(state: State) -> Page:
    '''Show a blank exercise form.'''
    return exercise_form(state)


@route
def save_exercise(state: State, exercise_name: str, muscle_group: str,
                  sets: str, reps: str, weight: str) -> Page:
    '''Check and save an exercise. Use try/except to handle invalid number text.'''
    error = ""
    if not exercise_name.strip():
        error = "Enter an exercise name."
    elif len(exercise_name.strip()) > 60:
        error = "Keep the exercise name to 60 characters or fewer."
    elif muscle_group not in MUSCLE_GROUPS:
        error = "Choose a muscle group from the list."

    try:
        set_count = int(sets)
        rep_count = int(reps)
        pounds = float(weight)
    except (ValueError, OverflowError):
        error = "Enter whole numbers for sets and reps, and a number for weight."
    else:
        if not 1 <= set_count <= 1000 or not 1 <= rep_count <= 1000:
            error = "Sets and reps must each be whole numbers from 1 to 1,000."
        elif not 0 <= pounds <= 10000:
            error = "Weight must be a number from 0 to 10,000 pounds."

    if error:
        if muscle_group not in MUSCLE_GROUPS:
            muscle_group = "Chest"
        return exercise_form(state, error, exercise_name, muscle_group,
                             sets, reps, weight)

    state.entries.append(WorkoutEntry(exercise_name.strip(), muscle_group,
                                      set_count, rep_count, pounds))
    state.selected_muscle_group = "All"
    return history(state)


@route
def history(state: State) -> Page:
    '''Show saved exercises and delete buttons.'''
    content = [
        Paragraph("THE WORK YOU'VE PUT IN"),
        Header("Exercise history"),
        Paragraph("Look back at your lifts, or filter by muscle group."),
        Div([
            Label("Muscle group", "muscle_group"),
            SelectBox("muscle_group", ["All"] + list(MUSCLE_GROUPS),
                      state.selected_muscle_group),
            Button("Apply Filter", filter_history),
        ]),
    ]
    matching_count = 0
    for entry_index in range(len(state.entries)):
        entry = state.entries[entry_index]
        if (state.selected_muscle_group == "All"
                or entry.muscle_group == state.selected_muscle_group):
            matching_count += 1
            content.append(Div([
                Div([Header(entry.exercise_name, level=2),
                     Paragraph(entry_summary(entry))]),
                Button("Delete", delete_entry, {"entry_index": entry_index}),
            ]))
    if not state.entries:
        content.append(Paragraph("No exercises logged yet. Add your first exercise."))
    elif matching_count == 0:
        content.append(Paragraph("No entries match this muscle group. Try All."))
    else:
        content.append(Paragraph(str(matching_count) + " entries shown"))
    content.append(Div([Button("+ Log Exercise", log_exercise),
                        Button("Home", index)]))
    return site_page(state, content)


@route
def filter_history(state: State, muscle_group: str) -> Page:
    '''Filter exercises by muscle group.'''
    if muscle_group == "All" or muscle_group in MUSCLE_GROUPS:
        state.selected_muscle_group = muscle_group
    return history(state)


@route
def delete_entry(state: State, entry_index: int) -> Page:
    '''Delete the selected exercise.'''
    if 0 <= entry_index < len(state.entries):
        state.entries.pop(entry_index)
    return history(state)


@route
def statistics(state: State) -> Page:
    '''Show workout totals and goal progress.'''
    return site_page(state, [
        Paragraph("SEE YOUR EFFORT ADD UP"),
        Header("Your statistics"),
        Paragraph("Totals include every exercise, regardless of your history filter."),
        Div([
            metric("Exercises logged", str(len(state.entries))),
            metric("Total sets", str(total_sets(state.entries))),
            metric("Total lifting volume", f"{total_volume(state.entries):,.1f} lb"),
        ]),
        goal_card(state),
        Div([
            Header("What is lifting volume?", level=2),
            Paragraph("For each entry: sets × reps per set × weight in pounds."),
            Paragraph("For example, 3 sets × 10 reps × 95 lb = 2,850 lb of volume."),
            Paragraph("Unweighted entries count toward your set goal and add 0 lb of volume."),
        ]),
        Button("Home", index),
    ])


def settings_form(state: State, error: str = "", name: str = "",
                  set_goal: str = "") -> Page:
    '''Show settings inputs and any error.'''
    if not error:
        name = state.name
        set_goal = str(state.set_goal)
    content = [
        Paragraph("MAKE IT YOURS"),
        Header("Your settings"),
        Paragraph("Choose a name and a total-set goal for this log."),
    ]
    if error:
        content.append(Paragraph(error, role="alert"))
    content.append(Div([
        Div([Label("Your name", "name"), TextBox("name", name, maxlength=40)]),
        Div([Label("Total-set goal", "set_goal"), TextBox("set_goal", set_goal)]),
        Paragraph("Your goal counts sets across all entries in this log."),
        Div([Button("Save Settings", save_settings),
             Button("Home", index)]),
    ]))
    return site_page(state, content)


@route
def settings(state: State) -> Page:
    '''Show the settings page.'''
    return settings_form(state)


@route
def save_settings(state: State, name: str, set_goal: str) -> Page:
    '''Check and save the name and set goal.'''
    if not name.strip() or len(name.strip()) > 40:
        return settings_form(state, "Enter a name from 1 to 40 characters.", name, set_goal)
    try:
        goal = int(set_goal)
    except (ValueError, OverflowError):
        return settings_form(state, "Enter a whole number for your set goal.", name, set_goal)
    if not 1 <= goal <= 100000:
        return settings_form(state, "Your set goal must be from 1 to 100,000.", name, set_goal)
    state.name = name.strip()
    state.set_goal = goal
    return index(state)


start_server(State([], "Peter", 50, "All"))
