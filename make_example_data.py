"""Create entirely synthetic demo workbooks, not real university records."""
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent


def main():
    names = ["Demo Faculty A", "Demo Faculty B", "Demo Faculty C"]
    courses = pd.DataFrame([
        {"course_id": "DEMO101", "course_name": "Example Python", "Doctors_Names": names[0]},
        {"course_id": "DEMO102", "course_name": "Example Statistics", "Doctors_Names": names[1]},
        {"course_id": "DEMO103", "course_name": "Example Databases", "Doctors_Names": names[2]},
    ])
    availability = pd.DataFrame([
        {"Doctors_Names": name, "available": day}
        for name in names for day in ["Saturday", "Sunday", "Monday"]
    ])
    registrations = pd.DataFrame([
        {"Student_id": student, "course_id": row["course_id"],
         "course_name": row["course_name"], "Doctors_Names": row["Doctors_Names"],
         "class room_name": "Demo Room " + str(index + 1)}
        for student in [1001, 1002]
        for index, row in courses.iterrows()
    ])
    for filename, frame in [
        ("Courses.xlsx", courses),
        ("Doctors_availability.xlsx", availability),
        ("IDs&Courses.xlsx", registrations),
    ]:
        target = BASE / filename
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite {target.name}; move it aside first.")
    for filename, frame in [
        ("Courses.xlsx", courses),
        ("Doctors_availability.xlsx", availability),
        ("IDs&Courses.xlsx", registrations),
    ]:
        frame.to_excel(BASE / filename, index=False)
    print("Created synthetic demo data. Demo students: 1001 and 1002.")


if __name__ == "__main__":
    main()
