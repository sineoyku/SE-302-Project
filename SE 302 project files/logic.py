import threading
import time
import random
import os

from db import DB
from collections import defaultdict
from models import Course, Classroom
import data_access

class ScheduleSystem:
    def __init__(self):
        self.reset_data()
        db_path = os.path.join(os.path.dirname(__file__), "examtable.db")
        self.db = DB(db_path)

    def reset_data(self):
        self.courses = []
        self.classrooms = []
        self.all_students_list = set()
        self.num_days = 7
        self.slots_per_day = 4
        self.assignments = {}
        self.student_room_map = {}
        self.room_schedule = defaultdict(set)
        self.stop_event = threading.Event()
        self.conflict_matrix = defaultdict(set)
        self.room_usage_count = defaultdict(int)
        self.slot_usage_count = defaultdict(int)
        self.iteration_count = 0
        self.MAX_ITERATIONS = 200000

    def load_classrooms_regex(self, filepath):
        try:
            self.classrooms = data_access.read_classrooms_from_file(filepath)
            if not self.classrooms: return "WARNING: 0 classrooms found."
            return f"SUCCESS: {len(self.classrooms)} classrooms."
        except Exception as e: return f"ERROR: {e}"

    def load_courses_regex(self, filepath):
        try:
            self.courses = data_access.read_courses_from_file(filepath)
            if not self.courses: return "WARNING: 0 courses found."
            return f"SUCCESS: {len(self.courses)} courses."
        except Exception as e: return f"ERROR: {e}"

    def load_all_students_regex(self, filepath):
        try:
            self.all_students_list = data_access.read_students_from_file(filepath)
            return f"SUCCESS: {len(self.all_students_list)} students."
        except Exception as e: return f"ERROR: {e}"

    def validate_feasibility(self):
        total_slots = self.num_days * self.slots_per_day
        total_school_capacity = sum(r.capacity for r in self.classrooms)
        total_capacity_over_time = total_slots * total_school_capacity
        needed_seats = sum(len(c.students) for c in self.courses)
        if needed_seats > total_capacity_over_time:
            return False, f"IMPOSSIBLE: Need {needed_seats} seats, total capacity is {total_capacity_over_time}."
        return True, "OK"

    def build_conflict_matrix(self):
        self.conflict_matrix.clear()
        n = len(self.courses)
        for i in range(n):
            for j in range(i + 1, n):
                s1 = set(self.courses[i].students)
                s2 = set(self.courses[j].students)
                if not s1.isdisjoint(s2):
                    self.conflict_matrix[self.courses[i].code].add(self.courses[j].code)
                    self.conflict_matrix[self.courses[j].code].add(self.courses[i].code)

    def check_constraints(self, course, day, slot, student_agenda):
        for student in course.students:
            if student not in student_agenda or day not in student_agenda[student]:
                continue

            exams_today = student_agenda[student][day]

            # KURAL 1: Günde Max 2 Sınav
            if len(exams_today) >= 2: return False

            for s_assigned in exams_today:
                # KURAL 2: Aynı anda iki sınav OLAMAZ
                if s_assigned == slot: return False

                # KURAL 3: Ardışık sınav OLAMAZ (GUI saatleri sıraya dizdiği için bu formül hep doğru çalışır)
                if abs(s_assigned - slot) == 1: return False

        return True

    def find_rooms(self, course, day, slot):
        used_rooms_codes = self.room_schedule.get((day, slot), set())
        available = [r for r in self.classrooms if r.code not in used_rooms_codes]
        if not available: return None
        available.sort(key=lambda r: (self.room_usage_count[r.code], -r.capacity))
        selected = []
        current_cap = 0
        needed = len(course.students)
        for room in available:
            selected.append(room)
            current_cap += room.capacity
            if current_cap >= needed: return selected
        return None

    def distribute_students(self):
        self.student_room_map = {}
        for c_code, (d, s, rooms) in self.assignments.items():
            c = next(x for x in self.courses if x.code == c_code)
            students_to_seat = list(c.students)
            student_idx = 0
            for room in rooms:
                remaining = len(students_to_seat) - student_idx
                take = min(room.capacity, remaining)
                seated = students_to_seat[student_idx : student_idx + take]
                student_idx += take
                for stud in seated:
                    self.student_room_map[(stud, c_code)] = room.code
                if student_idx >= len(students_to_seat): break

    def save_data_to_db(self):
        # classrooms
        cls = [(r.code, r.capacity) for r in self.classrooms]
        self.db.save_classrooms(cls)

        # courses + course_students
        crs = [(c.code, c.students) for c in self.courses]
        self.db.save_courses_and_students(crs)

        # students (AYRI TABLO)
        if self.all_students_list:
            self.db.save_students(self.all_students_list)

    def load_data_from_db(self):
        # classrooms
        cls = self.db.load_classrooms()
        self.classrooms = [Classroom(code, cap) for code, cap in cls]
        # students
        students = self.db.load_students()
        self.all_students_list = set(students)

        # courses + students
        crs = self.db.load_courses_with_students()
        self.courses = [Course(code, students) for code, students in crs]

    def solve(self):
        self.assignments = {}
        self.room_schedule = defaultdict(set)
        self.room_usage_count = defaultdict(int)
        self.slot_usage_count = defaultdict(int)
        self.stop_event.clear()
        self.iteration_count = 0

        if not self.courses: return False, "No Data"
        is_feasible, msg = self.validate_feasibility()
        if not is_feasible: return False, msg
        self.build_conflict_matrix()

        random.shuffle(self.courses) # Rastgelelik
        sorted_courses = sorted(self.courses, key=lambda c: (len(c.students), len(self.conflict_matrix[c.code])), reverse=True)

        student_agenda = defaultdict(lambda: defaultdict(list))
        start_time = time.time()
        print("Calculation Started...")

        if self._backtrack(sorted_courses, 0, student_agenda):
            self.distribute_students()
            return True, f"Found Solution! ({round(time.time()-start_time, 2)} s)"
        elif self.stop_event.is_set():
            return False, "Stopped by user."
        else:
            return False, "No Solution Found."

    def _backtrack(self, course_list, index, student_agenda):
        if self.stop_event.is_set(): return False
        self.iteration_count += 1
        if self.iteration_count > self.MAX_ITERATIONS: return False

        if index == len(course_list): return True
        course = course_list[index]

        all_slots = [(d, s) for d in range(self.num_days) for s in range(self.slots_per_day)]

        # Dengeli Dağıtım (Boş slotları tercih et)
        all_slots.sort(key=lambda x: self.slot_usage_count[x])

        for d, s in all_slots:
            if not self.check_constraints(course, d, s, student_agenda): continue
            rooms = self.find_rooms(course, d, s)
            if not rooms: continue

            self.assignments[course.code] = (d, s, rooms)
            self.slot_usage_count[(d,s)] += 1
            if (d, s) not in self.room_schedule: self.room_schedule[(d,s)] = set()
            for r in rooms:
                self.room_schedule[(d,s)].add(r.code)
                self.room_usage_count[r.code] += 1

            affected_students = []
            for stud in course.students:
                if d not in student_agenda[stud]: student_agenda[stud][d] = []
                student_agenda[stud][d].append(s)
                affected_students.append(stud)

            if self._backtrack(course_list, index + 1, student_agenda): return True

            del self.assignments[course.code]
            self.slot_usage_count[(d,s)] -= 1
            for r in rooms:
                self.room_schedule[(d,s)].remove(r.code)
                self.room_usage_count[r.code] -= 1
            for stud in affected_students: student_agenda[stud][d].remove(s)
        return False