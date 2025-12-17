import re
from models import Course, Classroom

def read_classrooms_from_file(filepath):
    classrooms = []
    content = ""
    for enc in ['utf-8', 'cp1254', 'latin-1']:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
                break
        except:
            continue

    matches = re.findall(r"(Classroom_\d+)[^0-9]+(\d+)", content)
    for name, cap in matches:
        classrooms.append(Classroom(name, cap))

    return classrooms

def read_courses_from_file(filepath):
    courses = []
    content = ""
    for enc in ['utf-8', 'cp1254', 'latin-1']:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
                break
        except:
            continue

    # Satır satır oku
    lines = content.split('\n')
    current_code = None

    for line in lines:
        line = line.strip()
        if not line: continue

        # Ders kodunu bul (Örn: CourseCode_01)
        if "CourseCode_" in line:
            # Satırdan sadece kodu çek
            parts = line.split(';')
            for p in parts:
                if "CourseCode_" in p:
                    current_code = p.strip()
            continue

        # Öğrencileri bul (Std_ID_01)
        if current_code and "Std_ID_" in line:
            students_in_line = re.findall(r"(Std_ID_\d+)", line)
            if students_in_line:
                # Aynı ders koduyla daha önce kayıt var mı?
                existing = next((c for c in courses if c.code == current_code), None)
                if existing:
                    existing.students.extend(students_in_line)
                    existing.students = list(set(existing.students))
                else:
                    courses.append(Course(current_code, students_in_line))

    return courses

def read_students_from_file(filepath):
    # Bu sadece istatistik için, hesaplamada kritik değil
    all_students_list = set()
    content = ""
    for enc in ['utf-8', 'cp1254', 'latin-1']:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
                break
        except:
            continue

    matches = re.findall(r"(Std_ID_\d+)", content)
    for s_id in matches:
        all_students_list.add(s_id)

    return all_students_list