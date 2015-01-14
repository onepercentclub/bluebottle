from bluebottle.test.utils import BluebottleTestCase
from django.test import TestCase
from bluebottle.test.factory_models.tasks import SkillFactory, TaskFactory, TaskMemberFactory


class TestTaskMemberCase(BluebottleTestCase):
        
    def test_check_number_of_members_needed_no_externals_count(self):
        """ Test that 'check_number_of_members_needed' returns the right count without externals"""
        task = TaskFactory.create(status='open', people_needed=4)

        task_member1 = TaskMemberFactory.create(task=task, status='accepted')
        self.assertEqual(task_member1.check_number_of_members_needed(task), 1)

        task_member2 = TaskMemberFactory.create(task=task, status='accepted')
        self.assertEqual(task_member2.check_number_of_members_needed(task), 2)
        self.assertEqual(task_member1.check_number_of_members_needed(task), 2)


    def test_check_number_of_members_needed_with_externals_count(self):
        """ Test that 'check_number_of_members_needed' returns the right count with externals"""
        task = TaskFactory.create(status='open', people_needed=4)

        task_member1 = TaskMemberFactory.create(task=task, status='accepted', externals=1)
        self.assertEqual(task_member1.check_number_of_members_needed(task), 2)

        task_member2 = TaskMemberFactory.create(task=task, status='accepted', externals=2)
        self.assertEqual(task_member2.check_number_of_members_needed(task), 5)
        self.assertEqual(task_member1.check_number_of_members_needed(task), 5)

    def test_check_number_of_members_needed_set_in_progress(self):
        """ Test that the task status changes when enough people are accepted for a task. It shouldn't update 
            when insufficient people are accepted."""
        task = TaskFactory.create(status='open', people_needed=4)

        task_member1 = TaskMemberFactory.create(task=task, status='accepted', externals=1)

        self.assertEqual(task_member1.check_number_of_members_needed(task), 2)
        # Not enough people yet
        self.assertEqual(task.status, 'open')

        task_member2 = TaskMemberFactory.create(task=task, status='accepted', externals=2)

        self.assertEqual(task_member2.check_number_of_members_needed(task), 5)
        # More than people_needed have applied
        self.assertEqual(task.status, 'in progress')


class TestTaskCase(BluebottleTestCase):
    
    def test_save_check_status_update_insufficent_accepted_members(self):
        """ Check that the save method correctly sets the status of the task if not enough task members are 
            accepted for the task and the save method is called """
        task = TaskFactory.create(status='open', people_needed=4)
        task_member1 = TaskMemberFactory.create(task=task, status='accepted', externals=1)
        task.save()

        self.assertEqual(task.status, 'open')

        task_member2 = TaskMemberFactory.create(task=task, status='accepted')
        task.save()

        # Total of 3 out of 4 people. Task status should be open.
        self.assertEqual(task.status, 'open')

    def test_save_check_status_update_sufficent_accepted_members(self):
        """ Check that the save method correctly sets the status of the task if enough task members are 
            accepted for the task and the save method is called """
        task = TaskFactory.create(status='open', people_needed=2)
        task_member1 = TaskMemberFactory.create(task=task, status='accepted', externals=1)
        task.save()

        self.assertEqual(task.status, 'in progress')
