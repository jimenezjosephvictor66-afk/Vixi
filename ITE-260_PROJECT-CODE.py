import json
import os

# make sure the table lines print correctly in the terminal
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

# ---------------- SETTINGS ----------------
ADMIN_PASS = "admin123"   # only the admin knows this
PERIODS = ("p1", "p2", "p3")
# data.json is saved in the SAME folder as this .py file,
# no matter where you run the program from
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    BASE_DIR = os.getcwd()
DATA_FILE = os.path.join(BASE_DIR, "data.json")

# ---------------- DATA ----------------
# subjects = { "IT101": {"name": "Intro to Computing", "units": 3,
#                        "teacher": "Mr. Reyes",
#                        "students": ["2026-001"],
#                        "grades": {"2026-001": {"p1": 80, "p2": 85, "p3": 90}}} }
subjects = {}
students = {}   # { "2026-001": "Juan Dela Cruz" }
sections = {}   # { "BSIT-1A": ["2026-001", "2026-002"] }

# MESSAGE RULES
#   "Incorrect ..." -> what you typed does not match anything in the system
#   "Invalid ..."   -> what you typed is empty, the wrong format or not allowed
# After a mistake the program shows the message and asks ONLY THAT SAME INPUT
# again (it does not go back to the start). Type  cancel  to go back to the menu.


def load_data():
    global subjects, students, sections
    if not os.path.exists(DATA_FILE):
        print("No saved data yet. Starting fresh.")
        return
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        subjects = data["subjects"]
        students = data["students"]
        # old save files have no sections yet
        sections = data.get("sections", {})
        for info in subjects.values():
            # make sure old data has a grades section
            info.setdefault("grades", {})
            # old save files stored ONE grade per student; convert it
            # to P1/P2/P3 so the new grade table works
            for sid, g in list(info["grades"].items()):
                if not isinstance(g, dict):
                    info["grades"][sid] = {"p1": g, "p2": g, "p3": g}
        print(f"Loaded {len(subjects)} subject(s), {len(sections)} section(s) "
              f"and {len(students)} student(s).")
    except (json.JSONDecodeError, KeyError):
        print("Saved file is damaged. Starting fresh.")


def save_data():
    try:
        with open(DATA_FILE, "w") as f:
            json.dump({"subjects": subjects, "students": students,
                       "sections": sections}, f, indent=4)
    except OSError:
        print("WARNING: Could not save data. Check the folder permissions.")


# ---------------- HELPERS ----------------
def line():
    print("=" * 45)


def pause():
    input("\nPress Enter to continue...")


class Cancelled(Exception):
    """Raised when the user types 'cancel' at an input."""


def ask(prompt, check=None, fmt=None):
    """Ask for ONE input and keep asking only this input until it is correct.

    check(text) returns an error message, or None when the text is fine.
    fmt is applied to the text first (for example str.upper)."""
    while True:
        text = input(prompt).strip()
        if text.lower() == "cancel":
            raise Cancelled
        if fmt:
            text = fmt(text)
        error = check(text) if check else None
        if error is None:
            return text
        print(f"{error} (type 'cancel' to go back)")


def not_empty(message):
    return lambda t: None if t else message


def confirm(prompt):
    """y/n question. Returns True for y. 'n' prints Cancelled and gives False."""
    answer = ask(prompt,
                 lambda t: None if t in ("y", "n") else "Invalid choice. Type y or n.",
                 fmt=str.lower)
    if answer == "n":
        print("Cancelled.")
        return False
    return True


def parse_grade(text):
    """Return the grade as a float, or None if it is not a number 0-100."""
    try:
        grade = float(text)
    except ValueError:
        return None
    if not (0 <= grade <= 100):      # also rejects nan / inf
        return None
    return grade


def check_grade(text):
    return None if parse_grade(text) is not None \
        else "Invalid grade. Enter a number from 0 to 100."


def check_grade_or_skip(text):
    return None if text == "" else check_grade(text)


def check_units(text):
    try:
        units = int(text)
    except ValueError:
        return "Invalid units. Enter a whole number."
    return None if units >= 1 else "Invalid units. Must be at least 1."


def show_subjects():
    if not subjects:
        print("No subjects yet.")
        return False
    print(f"{'CODE':<8}{'SUBJECT':<22}{'UNITS':<6}")
    print("-" * 45)
    for code, info in subjects.items():
        print(f"{code:<8}{info['name']:<22}{info['units']:<6}")
    return True


def show_sections():
    if not sections:
        print("No sections yet.")
        return False
    print(f"{'SECTION':<14}STUDENTS")
    print("-" * 45)
    for name, members in sections.items():
        print(f"{name:<14}{len(members)}")
    return True


def get_section(student_id):
    """Return the section name of a student, or None."""
    for name, members in sections.items():
        if student_id in members:
            return name
    return None


def remarks(grade):
    return "PASSED" if grade >= 80 else "FAILED"


def final_grade(info, sid):
    """Average of P1, P2, P3. Returns None until all three are encoded."""
    g = info["grades"].get(sid)
    if not g:
        return None
    values = [g.get(p) for p in PERIODS]
    if any(v is None for v in values):
        return None
    return sum(values) / len(values)


def fmt_period(v):
    return "--" if v is None else f"{v:g}"


def fmt_final(v):
    return "--" if v is None else f"{v:.2f}"


def print_table(headers, widths, rows):
    """Draw a simple table with solid straight lines."""
    def border(left, mid, right):
        return left + mid.join("─" * (w + 2) for w in widths) + right

    def row(cells):
        return "│" + "│".join(f" {str(c)[:w]:<{w}} "
                              for c, w in zip(cells, widths)) + "│"

    print(border("┌", "┬", "┐"))
    print(row(headers))
    print(border("├", "┼", "┤"))
    for r in rows:
        print(row(r))
    print(border("└", "┴", "┘"))


def print_grade_table(info, student_ids):
    """Table: Student ID | Student Name | P1 | P2 | P3 | Final | Remarks"""
    rows = []
    for sid in student_ids:
        g = info["grades"].get(sid, {})
        fin = final_grade(info, sid)
        rem = remarks(fin) if fin is not None else "--"
        rows.append([sid, students[sid],
                     fmt_period(g.get("p1")),
                     fmt_period(g.get("p2")),
                     fmt_period(g.get("p3")),
                     fmt_final(fin), rem])
    print_table(["STUDENT ID", "STUDENT NAME", "P1", "P2", "P3",
                 "FINAL", "REMARKS"],
                [16, 28, 6, 6, 6, 7, 8], rows)


def print_report_card(sid):
    """Student table: Subject Code | Teacher | Periods | Final Grade + General Average."""
    enrolled = [(code, info) for code, info in subjects.items()
                if sid in info["students"]]
    if not enrolled:
        print("You are not enrolled in any subject yet.")
        return

    cw, tw, pw, fw = 12, 24, 6, 7            # column widths
    c, t, p, f = cw + 2, tw + 2, pw + 2, fw + 2   # widths with padding
    span = len(PERIODS) * p + (len(PERIODS) - 1)

    def cell(text, w):
        return f" {str(text)[:w]:^{w}} "

    def period_line(left, mid, right):
        return left + mid.join("─" * p for _ in PERIODS) + right

    # ---- header ----
    print("┌" + "─" * c + "┬" + "─" * t + "┬" + "─" * span + "┬" + "─" * f + "┐")
    print("│" + cell("SUBJECT CODE", cw) + "│" + cell("TEACHER", tw) + "│"
          + cell("PERIOD", span - 2) + "│" + cell("FINAL", fw) + "│")
    print("│" + " " * c + "│" + " " * t + period_line("├", "┬", "┤")
          + cell("GRADE", fw) + "│")
    print("│" + " " * c + "│" + " " * t + "│"
          + "│".join(cell(k.upper(), pw) for k in PERIODS) + "│"
          + " " * f + "│")
    print("├" + "─" * c + "┼" + "─" * t + period_line("┼", "┼", "┼")
          + "─" * f + "┤")

    # ---- one row per subject ----
    finals = []
    for code, info in enrolled:
        g = info["grades"].get(sid, {})
        fin = final_grade(info, sid)
        if fin is not None:
            finals.append(fin)
        teacher = info["teacher"] or "Not assigned"
        print("│" + f" {code[:cw]:<{cw}} " + "│" + f" {teacher[:tw]:<{tw}} " + "│"
              + "│".join(cell(fmt_period(g.get(k)), pw) for k in PERIODS)
              + "│" + cell(fmt_final(fin), fw) + "│")

    # ---- general average ----
    general = sum(finals) / len(finals) if finals else None
    label_w = c + 1 + t + 1 + span
    print("├" + "─" * c + "┴" + "─" * t + period_line("┴", "┴", "┼")
          + "─" * f + "┤")
    print("│" + " " + "GENERAL AVERAGE".rjust(label_w - 2) + " " + "│"
          + cell(fmt_final(general), fw) + "│")
    print("└" + "─" * label_w + "┴" + "─" * f + "┘")


def enter_grades(info, student_ids):
    """Ask for P1, P2, P3 of each student. Enter skips.
    A wrong grade only asks that same grade again."""
    for sid in student_ids:
        print(f"\n{students[sid]} ({sid})")
        current = info["grades"].setdefault(sid, {})
        for p in PERIODS:
            old = current.get(p)
            entry = ask(f"  {p.upper()} (current: {fmt_period(old)}) "
                        f"- Enter to skip: ", check_grade_or_skip)
            if entry != "":
                current[p] = float(entry)


# =====================================================
#                    ADMIN PORTAL
# =====================================================
def add_subject():
    line()
    print("ADD SUBJECT")
    line()

    def check_code(t):
        if t == "":
            return "Invalid subject code."
        if t in subjects:
            return "Invalid. That subject code already exists."
        return None

    code = ask("Subject code (e.g. IT101): ", check_code, fmt=str.upper)
    name = ask("Subject name: ", not_empty("Invalid subject name."))
    units = int(ask("Units: ", check_units))

    subjects[code] = {"name": name, "units": units,
                      "teacher": None, "students": [], "grades": {}}
    save_data()
    print(f"\nSubject {code} - {name} added!")


def add_section():
    line()
    print("ADD SECTION")
    line()

    def check_name(t):
        if t == "":
            return "Invalid section name."
        if t in sections:
            return "Invalid. That section already exists."
        return None

    name = ask("Section name (e.g. BSIT-1A): ", check_name, fmt=str.upper)
    sections[name] = []
    save_data()
    print(f"\nSection {name} added!")


def assign_section():
    line()
    print("ASSIGN STUDENT TO SECTION")
    line()
    if not show_sections():
        print("Add a section first.")
        return

    name = ask("\nEnter section name: ",
               lambda t: None if t in sections else "Incorrect section name.",
               fmt=str.upper)

    def check_id(t):
        if t == "":
            return "Invalid student ID."
        if t in sections[name]:
            return "Invalid. Student is already in this section."
        return None

    student_id = ask("Student ID: ", check_id)

    if student_id not in students:
        students[student_id] = ask("New student. Enter full name: ",
                                   not_empty("Invalid name."))

    current = get_section(student_id)
    if current:
        print(f"{students[student_id]} is currently in section {current}.")
        if not confirm(f"Move to {name}? (y/n): "):
            return
        sections[current].remove(student_id)

    sections[name].append(student_id)
    save_data()
    print(f"\n{students[student_id]} assigned to section {name}!")


def assign_student():
    line()
    print("ASSIGN STUDENT TO SUBJECT")
    line()
    if not show_subjects():
        return

    code = ask("\nEnter subject code: ",
               lambda t: None if t in subjects else "Incorrect subject code.",
               fmt=str.upper)

    def check_id(t):
        if t == "":
            return "Invalid student ID."
        if t in subjects[code]["students"]:
            return "Invalid. Student is already in this subject."
        return None

    student_id = ask("Student ID: ", check_id)

    if student_id not in students:
        students[student_id] = ask("New student. Enter full name: ",
                                   not_empty("Invalid name."))

    subjects[code]["students"].append(student_id)
    save_data()
    print(f"\n{students[student_id]} assigned to {code}!")


def assign_teacher():
    line()
    print("ASSIGN TEACHER TO SUBJECT")
    line()
    if not show_subjects():
        return

    code = ask("\nEnter subject code: ",
               lambda t: None if t in subjects else "Incorrect subject code.",
               fmt=str.upper)

    current = subjects[code]["teacher"]
    if current:
        print(f"Current teacher: {current}")
        if not confirm("Replace teacher? (y/n): "):
            return

    teacher = ask("Teacher name: ", not_empty("Invalid teacher name."))

    subjects[code]["teacher"] = teacher
    save_data()
    print(f"\nTeacher {teacher} assigned to {code}!")


def remove_teacher():
    line()
    print("REMOVE TEACHER")
    line()
    assigned = {code: info["teacher"] for code, info in subjects.items()
                if info["teacher"]}
    if not assigned:
        print("No teachers assigned yet.")
        return

    print(f"{'CODE':<10}TEACHER")
    print("-" * 45)
    for code, teacher in assigned.items():
        print(f"{code:<10}{teacher}")

    print("\n1. Remove teacher from one subject")
    print("2. Remove a teacher from ALL of their subjects")
    print("0. Cancel")
    choice = ask("\nChoose: ",
                 lambda t: None if t in ("0", "1", "2") else "Invalid choice.")

    if choice == "1":
        code = ask("\nEnter subject code: ",
                   lambda t: None if t in assigned
                   else "Incorrect subject code. Choose one from the list.",
                   fmt=str.upper)
        if not confirm(f"Remove {assigned[code]} from {code}? (y/n): "):
            return
        teacher = assigned[code]
        subjects[code]["teacher"] = None
        save_data()
        print(f"\nTeacher {teacher} removed from {code}.")

    elif choice == "2":
        name = ask("\nTeacher name: ",
                   lambda t: None if any(v.lower() == t.lower()
                                         for v in assigned.values())
                   else "Incorrect teacher name.")
        codes = [code for code, t in assigned.items()
                 if t.lower() == name.lower()]
        print(f"{name} handles: {', '.join(codes)}")
        if not confirm("Remove from all of these subjects? (y/n): "):
            return
        for code in codes:
            subjects[code]["teacher"] = None
        save_data()
        print(f"\nTeacher {name} removed from {len(codes)} subject(s).")

    else:
        print("Cancelled.")


def remove_student():
    line()
    print("REMOVE STUDENT")
    line()
    if not students:
        print("No students yet.")
        return

    print(f"{'ID':<17}{'NAME':<29}SECTION")
    print("-" * 55)
    for sid, name in students.items():
        print(f"{sid:<17}{name:<29}{get_section(sid) or '--'}")

    student_id = ask("\nEnter student ID: ",
                     lambda t: None if t in students else "Incorrect student ID.")

    print(f"\nSelected: {students[student_id]} ({student_id})")
    print("1. Remove from one subject only")
    print("2. Delete from the whole system")
    print("0. Cancel")
    choice = ask("\nChoose: ",
                 lambda t: None if t in ("0", "1", "2") else "Invalid choice.")

    if choice == "1":
        enrolled = [code for code, info in subjects.items()
                    if student_id in info["students"]]
        if not enrolled:
            print("This student is not enrolled in any subject.")
            return

        print("\nEnrolled in:")
        for code in enrolled:
            print(f"  {code} - {subjects[code]['name']}")

        code = ask("\nEnter subject code: ",
                   lambda t: None if t in enrolled
                   else "Incorrect subject code. Choose one from the list.",
                   fmt=str.upper)

        if not confirm(f"Remove from {code}? (y/n): "):
            return

        subjects[code]["students"].remove(student_id)
        subjects[code]["grades"].pop(student_id, None)
        save_data()
        print(f"\n{students[student_id]} removed from {code}.")

    elif choice == "2":
        print("WARNING: This removes the student from ALL subjects")
        print("and sections, and deletes all of their grades.")
        if not confirm("Delete permanently? (y/n): "):
            return

        name = students[student_id]
        for info in subjects.values():
            if student_id in info["students"]:
                info["students"].remove(student_id)
            info["grades"].pop(student_id, None)
        for members in sections.values():
            if student_id in members:
                members.remove(student_id)
        del students[student_id]
        save_data()
        print(f"\n{name} has been deleted from the system.")

    else:
        print("Cancelled.")


def view_all():
    line()
    print("ALL SUBJECTS")
    line()
    if not subjects:
        print("No subjects yet.")
    for code, info in subjects.items():
        print(f"\n{code} - {info['name']} ({info['units']} units)")
        print(f"  Teacher : {info['teacher'] or 'Not assigned'}")
        if info["students"]:
            print("  Students:")
            for sid in info["students"]:
                print(f"    - {sid} | {students[sid]} "
                      f"| {get_section(sid) or 'No section'}")
        else:
            print("  Students: None")

    print()
    line()
    print("ALL SECTIONS")
    line()
    if not sections:
        print("No sections yet.")
    for name, members in sections.items():
        print(f"\n{name} ({len(members)} student(s))")
        if members:
            for sid in members:
                print(f"    - {sid} | {students[sid]}")
        else:
            print("    No students.")


def admin_menu():
    while True:
        line()
        print("ADMIN PORTAL")
        line()
        print("1. Add Subject")
        print("2. Add Section")
        print("3. Assign Student to Subject")
        print("4. Assign Student to Section")
        print("5. Assign Teacher")
        print("6. Remove Teacher")
        print("7. Remove Student")
        print("8. View All")
        print("0. Logout")
        choice = input("\nChoose: ").strip()

        try:
            if choice == "1":
                add_subject()
            elif choice == "2":
                add_section()
            elif choice == "3":
                assign_student()
            elif choice == "4":
                assign_section()
            elif choice == "5":
                assign_teacher()
            elif choice == "6":
                remove_teacher()
            elif choice == "7":
                remove_student()
            elif choice == "8":
                view_all()
            elif choice == "0":
                print("Logged out.")
                break
            else:
                print("Invalid choice.")
        except Cancelled:
            print("Cancelled.")
        except Exception:
            print("\nIncorrect input. Something went wrong.")
        pause()


def admin_login():
    line()
    print("ADMIN LOGIN")
    line()
    ask("Enter admin password: ",
        lambda t: None if t == ADMIN_PASS else "Incorrect password.")
    print("\nAccess granted. Welcome, Admin!")
    admin_menu()


# =====================================================
#                   TEACHER PORTAL
# =====================================================
def teacher_subjects(teacher_name):
    """Return the subject codes handled by this teacher."""
    result = []
    for code, info in subjects.items():
        if info["teacher"] and info["teacher"].lower() == teacher_name.lower():
            result.append(code)
    return result


def encode_grades(my_subjects):
    line()
    print("ENCODE GRADES")
    line()
    for code in my_subjects:
        print(f"{code} - {subjects[code]['name']}")

    code = ask("\nEnter subject code: ",
               lambda t: None if t in my_subjects else "Incorrect subject code.",
               fmt=str.upper)

    info = subjects[code]
    if not info["students"]:
        print("No students enrolled in this subject yet.")
        return

    try:
        enter_grades(info, info["students"])
    finally:
        save_data()          # keep the grades typed even if the teacher cancels
    print("\nGrades saved!")
    print()
    print_grade_table(info, info["students"])


def update_grade(my_subjects):
    line()
    print("UPDATE GRADE")
    line()
    for code in my_subjects:
        print(f"{code} - {subjects[code]['name']}")

    code = ask(f"\nEnter class ID (example: {my_subjects[0]}): ",
               lambda t: None if t in my_subjects else "Incorrect class ID.",
               fmt=str.upper)

    info = subjects[code]
    if not info["students"]:
        print("No students enrolled in this subject yet.")
        return

    print()
    print_grade_table(info, info["students"])

    sid = ask("\nEnter student ID: ",
              lambda t: None if t in info["students"] else "Incorrect student ID.")

    current = info["grades"].setdefault(sid, {})
    names = "/".join(p.upper() for p in PERIODS)
    changed = False
    while True:
        print(f"\n{students[sid]} ({sid})")
        print("  " + "   ".join(f"{p.upper()}: {fmt_period(current.get(p))}"
                                for p in PERIODS))
        period = ask(f"Period to update ({names}, Enter to finish): ",
                     lambda t: None if t == "" or t in PERIODS
                     else "Invalid period.",
                     fmt=str.lower)
        if period == "":
            break

        grade = float(ask(f"New {period.upper()} grade (0-100): ", check_grade))
        current[period] = grade
        changed = True
        save_data()
        print(f"{period.upper()} updated to {fmt_period(grade)}.")

    if changed:
        print()
        print_grade_table(info, [sid])


def view_class(my_subjects):
    line()
    print("CLASS LIST")
    line()
    for code in my_subjects:
        info = subjects[code]
        print(f"\n{code} - {info['name']}")
        if not info["students"]:
            print("  No students.")
            continue
        rows = []
        for sid in info["students"]:
            fin = final_grade(info, sid)
            rem = remarks(fin) if fin is not None else "No grade yet"
            rows.append([sid, students[sid], get_section(sid) or "--",
                         fmt_final(fin), rem])
        print_table(["STUDENT ID", "STUDENT NAME", "SECTION", "FINAL",
                     "REMARKS"],
                    [16, 28, 14, 7, 12], rows)


def view_grades(my_subjects):
    line()
    print("VIEW GRADES")
    line()
    if not show_sections():
        return

    # 1) the teacher inputs a section
    sec = ask("\nEnter section: ",
              lambda t: None if t in sections else "Incorrect section name.",
              fmt=str.upper)

    # 2) inside the section, the teacher inputs a class ID (subject code)
    print()
    for code in my_subjects:
        print(f"{code} - {subjects[code]['name']}")
    code = ask(f"\nEnter class ID (example: {my_subjects[0]}): ",
               lambda t: None if t in my_subjects else "Incorrect class ID.",
               fmt=str.upper)

    info = subjects[code]
    class_students = [sid for sid in info["students"]
                      if sid in sections[sec]]
    if not class_students:
        print(f"\nNo students from section {sec} are enrolled in {code}.")
        return

    # 3) the teacher sees the table of grades
    while True:
        print()
        line()
        print(f"{code} - {info['name']} | Section {sec}")
        line()
        print_grade_table(info, class_students)

        # 4) the teacher can input P1, P2, P3 (final grade is computed)
        if not confirm("\nInput / edit grades? (y/n): "):
            break

        try:
            enter_grades(info, class_students)
        finally:
            save_data()      # keep the grades typed even if the teacher cancels
        print("\nGrades saved!")


def teacher_menu(name, my_subjects):
    while True:
        line()
        print(f"TEACHER PORTAL - {name}")
        line()
        print("1. Encode Grades")
        print("2. Update Grade")
        print("3. View Class List")
        print("4. View Grades")
        print("0. Logout")
        choice = input("\nChoose: ").strip()

        try:
            if choice == "1":
                encode_grades(my_subjects)
            elif choice == "2":
                update_grade(my_subjects)
            elif choice == "3":
                view_class(my_subjects)
            elif choice == "4":
                view_grades(my_subjects)
            elif choice == "0":
                print("Logged out.")
                break
            else:
                print("Invalid choice.")
        except Cancelled:
            print("Cancelled.")
        except Exception:
            print("\nIncorrect input. Something went wrong.")
        pause()


def teacher_login():
    name = ask("Teacher name: ",
               lambda t: None if teacher_subjects(t)
               else "Incorrect teacher name. No subjects assigned to that name.")
    teacher_menu(name, teacher_subjects(name))


# =====================================================
#                   STUDENT PORTAL
# =====================================================
def student_login():
    sid = ask("Student ID: ",
              lambda t: None if t in students else "Incorrect student ID.")

    line()
    print(f"{students[sid]} ({sid})")
    print(f"Section: {get_section(sid) or 'Not assigned'}")
    line()
    print_report_card(sid)
    pause()


# =====================================================
#                       MAIN
# =====================================================
def main():
    print(f"Data file: {DATA_FILE}")
    load_data()
    while True:
        line()
        print("GRADE TRACKING SYSTEM")
        line()
        print("1. Admin")
        print("2. Teacher")
        print("3. Student")
        print("0. Exit")
        choice = input("\nLogin as: ").strip()

        try:
            if choice == "1":
                admin_login()
            elif choice == "2":
                teacher_login()
            elif choice == "3":
                student_login()
            elif choice == "0":
                print("Goodbye!")
                break
            else:
                print("Invalid choice.")
        except Cancelled:
            print("Cancelled.")
        except Exception:
            print("\nIncorrect input. Something went wrong.")


main()