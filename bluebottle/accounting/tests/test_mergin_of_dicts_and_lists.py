from ..utils import mydict, mylist
from django.test import TestCase
from decimal import Decimal


class MyModel(object):
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def get_data(self, multiplier=1):
        return mydict(
            one=self.a * multiplier,
            two=self.b * multiplier,
            three=self.c * multiplier,
        )

    def get_nested_data(self):
        return mydict(
            one=self.a,
            two=self.b,
            list_of_dicts=mylist([self.get_data(), self.get_data(2)]),
            dict4=self.get_data(4)
        )


class DictTests(TestCase):

    def setUp(self):
        self.model111 = MyModel(1, 1, 1)
        self.model222 = MyModel(2, 2, 2)
        self.model123 = MyModel(1, 2, 3)
        self.models = [self.model111, self.model222, self.model123]

    def test_mydicts(self):
        totals_dict = mydict()

        for model in self.models:
            totals_dict += model.get_data()

        expected = mydict(
            one=4, # =1+2+1
            two=5, # =1+2+2
            three=6, # =1+2+3
        )
        self.assertDictEqual(totals_dict, expected)

    def test_nested_mydicts(self):
        totals_dict = mydict()

        for model in self.models:
            totals_dict += model.get_nested_data()

        self.assertEqual(totals_dict.get('one'), 4)
        self.assertEqual(totals_dict.get('two'), 5)

        expected_list = [
            mydict(
                one=4,
                two=5,
                three=6
            ),
            mydict(
                one=8,
                two=10,
                three=12,
            )
        ]
        self.assertEqual(totals_dict.get('list_of_dicts'), expected_list)

        expected_dict = mydict(
            one=16,
            two=20,
            three=24,
        )
        self.assertEqual(totals_dict.get('dict4'), expected_dict)

    def test_edge_cases(self):
        """
        -handling of None values

        -addition of decimals with integer or floats

        -addition of some Model with a Decimal equals None instead of error
        """

        dict1 = mydict(
            a=10,
            b=None,
            c=7,
            d=mylist([None, None]),
            e=mylist([Decimal('5.5'), 5.5, 5]),
            f=None,
            g=MyModel,
            h=MyModel,
            i=self.model111,
            j=MyModel(1, 1, 1),
        )
        dict2 = mydict(
            a=None,
            b=11,
            c=13,
            d=mylist([1, 2]),
            e=mylist([5, Decimal('5.1'), 5.5]),
            f=None,
            g=Decimal('10'),
            h=MyModel(1, 1, 1),
            i=self.model111,
            j=MyModel(1, 1, 2),
        )

        totals = dict1 + dict2

        expected = mydict(
            a=10,
            b=11,
            c=20,
            d=mylist([1, 2]),
            e=mylist([Decimal('10.5'), Decimal('10.6'), Decimal('10.5')]),
            f=None,
            g=None,
            h=None,
            i=None,
            j=None,
        )

        self.assertEqual(totals, expected)

    def test_structure_does_not_match(self):
        dict1 = mydict(a=1, b=2)
        dict2 = mydict(a=3)

        totals = dict1 + dict2
        self.assertEqual(totals, mydict())

        # dictionary keys are equal, but lists in the dict have different length
        dict3 = mydict(a=1, b=mylist([2, 3]))
        dict4 = mydict(a=3, b=mylist([3, 2, 5]))

        totals = dict3 + dict4
        self.assertEqual(totals, mydict(a=4, b=mylist()))

        # just repeat above logic for a good case to see if it passes
        dict5 = mydict(a=1, b=mylist([2, 3, 0]))
        dict6 = mydict(a=3, b=mylist([3, 2, 5]))
        totals = dict5 + dict6
        self.assertIsNotNone(totals)
        self.assertEqual(totals.get('b'), mylist([5, 5, 5]))
