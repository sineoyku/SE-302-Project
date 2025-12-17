import threading
import time
import random
from collections import defaultdict
import data_access

class ScheduleSystem:
    def __init__(self):
        self.reset_data()

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
        self.deadline = None   # ⏱️ TIMEOUT

    # ---------------- FILE LOADERS ----------------
    def load_classrooms_regex(self, filepath):
        try:
            self.classrooms = data_access.read_classrooms_from_file(filepath)
            if not self.classrooms:
                return "WARNING: 0 classrooms found."
            return f"SUCCESS: {len(self.classrooms)} classrooms."
        except Exception as e:
            return f"ERROR: {e}"

    def load_courses_regex(self, filepath):
        try:
            self.courses = data_access.read_courses_from_file(filepath)
            if not self.courses:
                return "WARNING: 0 courses found."
            return f"SUCCESS: {len(self.courses)} courses."
        except Exception as e:
            return f"ERROR: {e}"

    def load_all_students_regex(self, filepath):
        try:
            self.all_students_list = data_access.read_students_from_file(filepath)
            return f"SUCCESS: {len(self.all_students_list)} students."
        except Exception as e:
            return f"ERROR: {e}"

    # ---------------- VALIDATION ----------------
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
        student_sets = {c.code: set(c.students) for c in self.courses}

        n = len(self.courses)
        for i in range(n):
            for j in range(i + 1, n):
                if not student_sets[self.courses[i].code].isdisjoint(
                    student_sets[self.courses[j].code]
                ):
                    self.conflict_matrix[self.courses[i].code].add(self.courses[j].code)
                    self.conflict_matrix[self.courses[j].code].add(self.courses[i].code)

    # ---------------- CONSTRAINTS ----------------
    def check_constraints(self, course, day, slot, student_agenda):
        for student in course.students:
            if student not in student_agenda or day not in student_agenda[student]:
                continue

            exams_today = student_agenda[student][day]

            if len(exams_today) >= 2:
                return False

            for s_assigned in exams_today:
                if s_assigned == slot:
                    return False
                if abs(s_assigned - slot) == 1:
                    return False

        return True

    # ---------------- ROOMS ----------------
    def find_rooms(self, course, day, slot):
        used_rooms_codes = self.room_schedule.get((day, slot), set())
        available = [r for r in self.classrooms if r.code not in used_rooms_codes]

        if not available:
            return None

        available.sort(key=lambda r: (self.room_usage_count[r.code], -r.capacity))

        selected = []
        current_cap = 0
        needed = len(course.students)

        for room in available:
            selected.append(room)
            current_cap += room.capacity
            if current_cap >= needed:
                return selected

        return None

    # ---------------- DISTRIBUTION ----------------
    def distribute_students(self):
        self.student_room_map = {}

        for c_code, (d, s, rooms) in self.assignments.items():
            c = next((x for x in self.courses if x.code == c_code), None)
            if c is None:
                continue

            students_to_seat = list(c.students)
            idx = 0

            for room in rooms:
                remaining = len(students_to_seat) - idx
                take = min(room.capacity, remaining)
                seated = students_to_seat[idx : idx + take]
                idx += take

                for stud in seated:
                    self.student_room_map[(stud, c_code)] = room.code

                if idx >= len(students_to_seat):
                    break

    # ---------------- SOLVER ----------------
    def solve(self, time_limit_sec=5):
        try:
            self.assignments.clear()
            self.room_schedule.clear()
            self.room_usage_count.clear()
            self.slot_usage_count.clear()
            self.stop_event.clear()
            self.iteration_count = 0

            if not self.courses:
                return False, "No Data"

            feasible, msg = self.validate_feasibility()
            if not feasible:
                return False, msg

            self.build_conflict_matrix()

            random.shuffle(self.courses)
            sorted_courses = sorted(
                self.courses,
                key=lambda c: (len(c.students), len(self.conflict_matrix[c.code])),
                reverse=True
            )

            student_agenda = defaultdict(lambda: defaultdict(list))
            self.deadline = time.time() + time_limit_sec
            start_time = time.time()

            if self._backtrack(sorted_courses, 0, student_agenda):
                self.distribute_students()
                return True, f"Found Solution! ({round(time.time() - start_time, 2)} s)"

            if self.stop_event.is_set():
                return False, "Stopped (timeout or user)."

            return False, "No Solution Found."

        except Exception as e:
            return False, f"ERROR in solver: {e}"

    def _backtrack(self, course_list, index, student_agenda):
        if self.stop_event.is_set():
            return False

        if self.deadline and time.time() > self.deadline:
            self.stop_event.set()
            return False

        self.iteration_count += 1
        if self.iteration_count > self.MAX_ITERATIONS:
            return False

        if index == len(course_list):
            return True

        course = course_list[index]

        all_slots = [(d, s) for d in range(self.num_days) for s in range(self.slots_per_day)]
        all_slots.sort(key=lambda x: self.slot_usage_count[x])

        for d, s in all_slots:
            if not self.check_constraints(course, d, s, student_agenda):
                continue

            rooms = self.find_rooms(course, d, s)
            if not rooms:
                continue

            self.assignments[course.code] = (d, s, rooms)
            self.slot_usage_count[(d, s)] += 1

            for r in rooms:
                self.room_schedule[(d, s)].add(r.code)
                self.room_usage_count[r.code] += 1

            affected_students = []
            for stud in course.students:
                student_agenda[stud][d].append(s)
                affected_students.append(stud)

            if self._backtrack(course_list, index + 1, student_agenda):
                return True

            del self.assignments[course.code]
            self.slot_usage_count[(d, s)] -= 1

            for r in rooms:
                self.room_schedule[(d, s)].discard(r.code)
                self.room_usage_count[r.code] -= 1

            for stud in affected_students:
                student_agenda[stud][d].remove(s)

        return False
