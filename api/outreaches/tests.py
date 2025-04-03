from django.test import TestCase
from datetime import datetime, timedelta
from .utils import time_parts, add_minutes_to_time, get_task_interval_minutes, randomize_interval, get_first_time, get_next_time, not_in_interval, scheduler_tasks, put_within_working_hour, chron_parts
from unittest.mock import patch
import unittest

class TimeFunctionsTestCase(TestCase):
    def test_time_parts(self):
        test_time = datetime(year=2023, month=12, day=31, hour=10, minute=30)
        expected_parts = (2023, 12, 31, 10, 30)
        self.assertEqual(time_parts(test_time), expected_parts)

    def test_add_minutes_to_time(self):
        test_time = datetime(year=2023, month=12, day=31, hour=10, minute=30)
        added_time = add_minutes_to_time(test_time, 45)
        expected_time = datetime(year=2023, month=12, day=31, hour=11, minute=15)
        self.assertEqual(added_time, expected_time)

        # Test adding minutes crossing over to the next day
        test_time = datetime(year=2023, month=12, day=31, hour=23, minute=45)
        added_time = add_minutes_to_time(test_time, 30)
        expected_time = datetime(year=2024, month=1, day=1, hour=0, minute=15)
        self.assertEqual(added_time, expected_time)

        # Test adding minutes crossing over to the next month
        test_time = datetime(year=2023, month=12, day=31, hour=23, minute=45)
        added_time = add_minutes_to_time(test_time, 1000)
        expected_time = datetime(year=2024, month=1, day=1, hour=16, minute=25)
        self.assertEqual(added_time, expected_time)

        # Test adding minutes crossing over to the next year
        test_time = datetime(year=2023, month=12, day=31, hour=23, minute=59)
        added_time = add_minutes_to_time(test_time, 602)
        expected_time = datetime(year=2024, month=1, day=1, hour=10, minute=1)
        self.assertEqual(added_time, expected_time)

    def test_get_task_interval_minutes(self):
        self.assertEqual(get_task_interval_minutes(8, 4), 120)  # 8 hours per day, 4 tasks per day
        # Test case with 10 hours per day and 3 tasks per day
        self.assertEqual(get_task_interval_minutes(10, 3), 200)

        # Test case with 6 hours per day and 6 tasks per day (higher task density)
        self.assertEqual(get_task_interval_minutes(6, 6), 60)

        # Test case with 24 hours per day and 1 task per day (continuous work)
        self.assertEqual(get_task_interval_minutes(24, 1), 1440)

        # Test case with 0 hours per day and 0 tasks per day (edge case)
        self.assertEqual(get_task_interval_minutes(0, 0), 0)

        # Test case with negative values (invalid input)
        with self.assertRaises(ValueError):
            get_task_interval_minutes(-5, 3)

    def test_randomize_interval(self):
        """Tests multiple scenarios for the randomize_interval function.""" 

        # Scenario 1: Direction 0
        interval = randomize_interval(4, 0, 0)  # interval_minutes is now 4
        self.assertTrue(-1 <= interval <= 1)  # Range is +/- 25% of interval_minutes

        interval = randomize_interval(4, 60, 0)
        self.assertTrue(59 <= interval <= 61)  # Adjust the expectations

        # Scenario 2: Direction -1 (Similar changes)
        interval = randomize_interval(4, 0, -1)
        self.assertTrue(-1 <= interval <= 0)

        interval = randomize_interval(4, 60, -1)
        self.assertTrue(59 <= interval <= 60)

        # Scenario 3: Direction 1 (Similar changes)
        interval = randomize_interval(4, 0, 1)
        self.assertTrue(0 <= interval <= 1)

        interval = randomize_interval(4, 60, 1)
        self.assertTrue(60 <= interval <= 61)
    
    def test_zero_interval_minutes(self):
        result = randomize_interval(0, 10, direction=0)
        self.assertEqual(result, 10)  # Expect the seed_minutes to be returned directly

    def test_positive_interval(self):
        interval_minutes = 60
        seed_minutes = 10

        result = randomize_interval(interval_minutes, seed_minutes, direction=0)

        # Check that the result is within the expected range:
        self.assertGreaterEqual(result, seed_minutes - 15)
        self.assertLessEqual(result, seed_minutes + 15)

    def test_negative_interval_minutes(self):
        with self.assertRaises(ValueError) as cm:
            randomize_interval(-20, 10, direction=0)

        self.assertEqual(str(cm.exception), "interval_minutes and seed_minutes must be non-negative")

    def test_negative_seed_minutes(self):
        with self.assertRaises(ValueError) as cm:
            randomize_interval(20, -5, direction=0)

        self.assertEqual(str(cm.exception), "interval_minutes and seed_minutes must be non-negative")    
   

    def test_invalid_direction(self):
        with self.assertRaises(ValueError) as cm:
            randomize_interval(30, 0, direction=2)
        
        self.assertEqual(str(cm.exception), "Invalid direction. Direction should be -1, 0, or 1.")

    @patch('random.randint')
    def test_randomness(self, mock_randint):
        mock_randint.side_effect = [5, -5, 0]  # Control the output of randint
        interval_minutes = 20
        seed_minutes = 50

        # Run the function multiple times to test different 'random' values:
        result1 = randomize_interval(interval_minutes, seed_minutes, direction=0)
        result2 = randomize_interval(interval_minutes, seed_minutes, direction=-1)
        result3 = randomize_interval(interval_minutes, seed_minutes, direction=1)

        self.assertEqual(result1, 55)
        self.assertEqual(result2, 45)
        self.assertEqual(result3, 50)

    def test_get_first_time(self):
        start_time = datetime(year=2023, month=12, day=31, hour=10, minute=30)

        def test_different_interval_minutess(interval_minutes):
            first_time = get_first_time(start_time, interval_minutes)
            boundary_max = start_time + timedelta(minutes=int(0.25*interval_minutes))
            self.assertTrue(start_time <= first_time)  # First time should be later than start_time
            self.assertTrue(first_time <= boundary_max)
        test_different_interval_minutess(4)
        test_different_interval_minutess(8)
        test_different_interval_minutess(12)
        test_different_interval_minutess(40)

    def test_get_next_time(self):
        current_time = datetime(year=2023, month=12, day=31, hour=10, minute=30)
        next_time = get_next_time(current_time, 60)
        self.assertTrue(current_time < next_time)  # Next time should be later than current_time

        
    def test_normal_interval_inside(self):
        current_time = datetime(2023, 12, 30, 15, 0)
        start_time = 10  # Start hour
        end_time = 18   # End hour
        self.assertFalse(not_in_interval(current_time, start_time, end_time))

    def test_normal_interval_outside(self):
        current_time = datetime(2023, 12, 30, 6, 0)
        start_time = 10  # Start hour
        end_time = 18   # End hour
        self.assertTrue(not_in_interval(current_time, start_time, end_time))

    def test_edge_cases(self):
        current_start = datetime(2023, 12, 30, 10, 0)  # Right on the start boundary
        current_end = datetime(2023, 12, 30, 18, 0)    # Right on the end boundary
        start_time = 10
        end_time = 18

        self.assertFalse(not_in_interval(current_start, start_time, end_time))
        self.assertTrue(not_in_interval(current_end, start_time, end_time)) # end time is not inclusive

    def test_equal_start_stop(self):
        current_time = datetime(2023, 12, 30, 15, 0)
        start_time = 13  # Start hour
        end_time = 13  # End hour
        self.assertFalse(not_in_interval(current_time, start_time, end_time))

    def test_overnight_in_interval(self):
        current_time = datetime(2023, 12, 30, 2, 15)
        start_time = 23   # Start hour
        end_time = 5  # End hour
        self.assertFalse(not_in_interval(current_time, start_time, end_time))

    def test_overnight_outside_interval(self):
        current_time = datetime(2023, 12, 30, 10, 0) 
        start_time = 23  # Start hour
        end_time = 5  # End hour
        self.assertTrue(not_in_interval(current_time, start_time, end_time))
    
    @patch('outreaches.utils.randomize_interval')
    def test_positive_interval(self, mock_randomize_interval):
        current_time = datetime(2023, 12, 28, 14, 30)
        mock_randomize_interval.return_value = 20  # Control the random output

        result = get_next_time(current_time, interval_minutes=60)  # Assuming original interval_minutes is 60

        expected_result = current_time + timedelta(minutes=20)
        self.assertEqual(result, expected_result)

    @patch('outreaches.utils.randomize_interval')
    def test_interval_boundaries(self, mock_randomize_interval):
        current_time = datetime(2023, 12, 28, 14, 30)
        mock_randomize_interval.return_value = 0  # Minimum random value
        min_expected = current_time  # Should be the same as current_time

        result = get_next_time(current_time, interval_minutes=60) 
        self.assertEqual(result, min_expected)

        # mock_randomize_interval.return_value = 60  # Maximum random value (interval_minutes * 0.25)
        # max_expected = current_time + timedelta(minutes=60) 
        # result = get_next_time(current_time, interval_minutes=60) 
        # self.assertLess(result, max_expected)  # Ensure it doesn't reach the maximum

class SchedulerTestCase(TestCase):
    def test_scheduler_tasks(self):
        # Mocking necessary objects and functions for testing
        class Task:
            def __init__(self, name):
                self.name = name
                self.enabled = False
                self.crontab = None

        class CrontabSchedule:
            @classmethod
            def create(cls, **kwargs):
                return cls(**kwargs)

        def get_task_interval_minutes(hours_per_day, tasks_per_day):
            return 60  # Dummy implementation for testing

        def get_first_time(start_time, interval_minutes):
            return start_time  # Dummy implementation for testing

        def get_next_time(current_time, interval_minutes):
            return current_time  # Dummy implementation for testing

        # queryset = [
        #     Task(name="Task1"),
        #     Task(name="Task2"),
        #     Task(name="Task3"),
        # ]
        queryset = [Task(name=f"Task{i}") for i in range(1, 51)]

        start_time = datetime(year=2023, month=12, day=31, hour=8, minute=0)
        hours_per_day = 8
        tasks_per_day = 3
        daily_start_time = 14
        daily_end_time = 2

        result = scheduler_tasks(queryset, start_time, hours_per_day, tasks_per_day, daily_start_time, daily_end_time)
        # for task in result:

        # Assertions
        self.assertEqual(len(result), 50)  # Ensure all tasks are processed
        print()
        for task in result:
            
            self.assertTrue(task.enabled)  # Ensure tasks are enabled
            self.assertIsNotNone(task.crontab)  # Ensure crontab is set
            year, month, day, hour, minute = chron_parts(task.crontab)
            
            task_time = datetime(year=year, month=month, day=day, hour=hour, minute=minute)
            print(task.crontab)
            within_nonworking_hours = not_in_interval(task_time, daily_start_time, daily_end_time) # should be false
            self.assertFalse(within_nonworking_hours)  # Task time should be within working hours


class TestPutWithinWorkingHour(unittest.TestCase):

    def test_put_within_working_hour(self):
        # Test case where current_task_time is within working hours (9 AM to 5 PM)
        current_task_time = datetime(year=2023, month=12, day=31, hour=12, minute=0)
        start_hour = 9
        stop_hour = 17
        num_working_hours = stop_hour - start_hour
        num_not_working_hours = 24 - num_working_hours
        updated_task_time = put_within_working_hour(current_task_time, start_hour, stop_hour)
       
        self.assertEqual(updated_task_time, current_task_time)  # No change expected

        # Test case where current_task_time is outside working hours (6 PM)
        current_task_time = datetime(year=2023, month=12, day=31, hour=18, minute=0)
        updated_task_time = put_within_working_hour(current_task_time, start_hour, stop_hour)
        expected_time = current_task_time + timedelta(hours=num_not_working_hours)
        self.assertEqual(updated_task_time, expected_time)  # Adjusted to 10 AM next day

        # Test case where start_hour is greater than stop_hour (night shift)
        start_hour = 20
        stop_hour = 6
        current_task_time = datetime(year=2023, month=12, day=31, hour=5, minute=0)
        updated_task_time = put_within_working_hour(current_task_time, start_hour, stop_hour)
        self.assertEqual(updated_task_time, current_task_time)  # No change expected
        
        start_hour = 20
        stop_hour = 6
        current_task_time = datetime(year=2023, month=12, day=31, hour=20, minute=0)
        updated_task_time = put_within_working_hour(current_task_time, start_hour, stop_hour)
        
        self.assertEqual(updated_task_time, current_task_time)  # No change expected

        start_hour = 20
        stop_hour = 6

        working_interval = stop_hour - start_hour
        if stop_hour < start_hour:
            working_interval += 24
        not_working_interval = 24 - working_interval
        
        current_task_time = datetime(year=2023, month=12, day=31, hour=6, minute=55)
        updated_task_time = put_within_working_hour(current_task_time, start_hour=start_hour, stop_hour=stop_hour)
        expected_time = current_task_time + timedelta(hours=not_working_interval)
        self.assertEqual(updated_task_time, expected_time)

        current_task_time = datetime(year=2023, month=12, day=31, hour=5, minute=59)
        updated_task_time = put_within_working_hour(current_task_time, start_hour=start_hour, stop_hour=stop_hour)
        # expected_time = current_task_time + timedelta(hours=not_working_interval)
        self.assertEqual(updated_task_time, current_task_time) # no change expected


        current_task_time = datetime(year=2023, month=12, day=31, hour=6, minute=00)
        updated_task_time = put_within_working_hour(current_task_time, start_hour=start_hour, stop_hour=stop_hour)
        expected_time = current_task_time + timedelta(hours=not_working_interval)
        print(current_task_time, expected_time)
        self.assertEqual(updated_task_time, expected_time)
        
        current_task_time = datetime(year=2023, month=12, day=31, hour=19, minute=59)
        updated_task_time = put_within_working_hour(current_task_time, start_hour=start_hour, stop_hour=stop_hour)
        expected_time = current_task_time + timedelta(hours=not_working_interval)
        while not_in_interval(expected_time, start_hour, stop_hour):
            expected_time = expected_time + timedelta(hours=not_working_interval)
        print(current_task_time, expected_time)
        self.assertEqual(updated_task_time, expected_time)

        
        