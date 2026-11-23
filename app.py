from flask import Flask, render_template, request, jsonify
import pandas as pd
import random
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def data_file(name):
    return BASE_DIR / name

app = Flask(__name__)

def read_courses(file_path):
    return pd.read_excel(file_path)

def read_doctor_availability(file_path):
    return pd.read_excel(file_path)

def generate_master_timetable(courses_df, availability_df):
    timeslots = [
        "Saturday_9-10:40AM", "Saturday_10:40-12:20PM", "Saturday_1:10-2:50PM", "Saturday_2:50-4:30PM",
        "Sunday_9-10:40AM", "Sunday_10:40-12:20PM", "Sunday_1:10-2:50PM", "Sunday_2:50-4:30PM",
        "Monday_9-10:40AM", "Monday_10:40-12:20PM", "Monday_1:10-2:50PM", "Monday_2:50-4:30PM",
        "Tuesday_9-10:40AM", "Tuesday_10:40-12:20PM", "Tuesday_1:10-2:50PM", "Tuesday_2:50-4:30PM",
        "Wednesday_9-10:40AM", "Wednesday_10:40-12:20PM", "Wednesday_1:10-2:50PM", "Wednesday_2:50-4:30PM",
        "Thursday_9-10:40AM", "Thursday_10:40-12:20PM", "Thursday_1:10-2:50PM", "Thursday_2:50-4:30PM"
    ]

    random.shuffle(timeslots)
    master_timetable = {timeslot: [] for timeslot in timeslots}

    for _, row in courses_df.iterrows():
        course_id = row['course_id'].strip()
        course_name = row['course_name']
        doctor_name = row['Doctors_Names']
        available_days = availability_df[availability_df['Doctors_Names'] == doctor_name]['available'].tolist()
        available_timeslots = [f"{day}_{time.split('_')[1]}" for day in available_days for time in timeslots if day in time]

        for timeslot in available_timeslots:
            if len(master_timetable[timeslot]) < 2:
                master_timetable[timeslot].append((course_id, course_name, doctor_name))
                break
        else: 
            print(f"Warning: Unable to schedule course {course_id} ({course_name}) by {doctor_name}.")

    return master_timetable

def export_master_timetable(master_timetable, file_path):
    timetable_data = []
    for timeslot, courses in master_timetable.items():
        for course in courses:
            timetable_data.append({
                'Timeslot': timeslot,
                'Course ID': course[0],
                'Course Name': course[1],
                'Doctor Name': course[2]
            })

    timetable_df = pd.DataFrame(timetable_data)
    timetable_df.to_excel(file_path, index=False)

def get_registered_courses(student_id, file_path):
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip().str.replace('\t', '')
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.strip().str.replace('\t', '', regex=False)
    df['Student_id'] = pd.to_numeric(df['Student_id'], errors='coerce')
    registered_courses = df[df['Student_id'] == student_id]
    
    if registered_courses.empty:
        return None, None
    
    classroom_names = df[['course_id', 'class room_name']].drop_duplicates()
    return registered_courses, classroom_names

def retrieve_assigned_times(reg_courses, master_timetable):
    assigned_times = []
    for _, row in reg_courses.iterrows():
        course_id = row['course_id']
        for timeslot, courses in master_timetable.items():
            for course in courses:
                if course[0] == course_id:
                    assigned_times.append((course_id, course[1], course[2], timeslot))
    return assigned_times

def resolve_conflicts(assigned_times, master_timetable):
    timeslots_used = set()
    for course in assigned_times:
        timeslot = course[3]
        if timeslot in timeslots_used:
            for alt_timeslot in master_timetable.keys():
                if alt_timeslot not in timeslots_used:
                    timeslots_used.add(alt_timeslot)
                    assigned_times[assigned_times.index(course)] = (course[0], course[1], course[2], alt_timeslot)
                    break
        else:
            timeslots_used.add(timeslot)
    return assigned_times

def generate_master_table_html(master_timetable):
    """Generates the master table HTML for the director."""
    html_content = """
    <table border="1">
        <tr>
            <th>Timeslot</th>
            <th>Course ID</th>
            <th>Course Name</th>
            <th>Doctor Name</th>
        </tr>
    """
    for timeslot, courses in master_timetable.items():
        for course in courses:
            html_content += f"""
            <tr>
                <td>{timeslot}</td>
                <td>{course[0]}</td>
                <td>{course[1]}</td>
                <td>{course[2]}</td>
            </tr>
            """
    html_content += "</table>"
    return html_content

@app.route('/generate_timetable', methods=['POST'])
def generate_timetable():
    student_id = request.json['student_id']

    if student_id == '8':  # Demo-only master view, NOT authentication
        html_content = generate_master_table_html(master_timetable)  # Generate the master table HTML
        return jsonify({'html_content': html_content})
    else:
        registered_courses, classroom_names = get_registered_courses(int(student_id), data_file("IDs&Courses.xlsx"))
        if registered_courses is not None:
            # Retrieve assigned times for registered courses
            assigned_times = retrieve_assigned_times(registered_courses, master_timetable)
            # Resolve conflicts
            resolved_times = resolve_conflicts(assigned_times, master_timetable)

            days = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
            periods = ["9-10:40AM", "10:40-12:20PM", "12:20-1:10PM", "1:10-2:50PM", "2:50-4:30PM"]
            
            timetable_html_content = "<table border='1'>"
            timetable_html_content += "<tr><th>Day/Period</th>"
            for period in periods:
                timetable_html_content += f"<th>{period}</th>"
            timetable_html_content += "</tr>"
            
            for day in days:
                timetable_html_content += f"<tr><td>{day}</td>"
                for period in periods:
                    if period == "12:20-1:10PM":
                        timetable_html_content += "<td>Break</td>"
                    else:
                        timeslot = f"{day}_{period}"
                        courses_info = []
                        for course in resolved_times:
                            if course[3] == timeslot:
                                doctor_name = course[2]
                                classroom_name = classroom_names[classroom_names['course_id'] == course[0]]['class room_name'].iloc[0]
                                courses_info.append(
                                    f"{course[0]} ({classroom_name})<br><div class='doctor-name'>{doctor_name}</div>"
                                )
                        timetable_html_content += f"<td>{'<br>'.join(courses_info) if courses_info else ''}</td>"
                timetable_html_content += "</tr>"

            timetable_html_content += "</table>"

            return jsonify({'html_content': timetable_html_content})
        else:
            return jsonify({'html_content': 'No registered courses found for the entered student ID.'})

@app.route('/')
def index():
    return render_template('index.html')  # Make sure index.html exists

if __name__ == "__main__":
    courses_df = read_courses(data_file("Courses.xlsx"))
    availability_df = read_doctor_availability(data_file("Doctors_availability.xlsx"))

    master_timetable = generate_master_timetable(courses_df, availability_df)
    export_master_timetable(master_timetable, data_file("Master_Timetable.xlsx"))

    app.run(host="127.0.0.1", debug=False)
