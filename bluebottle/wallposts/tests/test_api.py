# from django.core.urlresolvers import reverse
# from rest_framework import status
# from rest_framework.test import APITestCase

# from bluebottle.test.factory_models.wallposts import TextWallPostFactory

# class TextWallPostTestCase(APITestCase)
#     """
#     Base class for test cases for ``text wall post`` module.

#     The testing classes for ``text wall post`` module related to the API must
#     subclass this.
#     """
#     def setUp(self):
#     	self.textwallpost = TextWallPostFactory.create()


# class TextWallPostListTestCase(TextWallPostTestCase)
#     """
#     Test case for ``TextWallPostList`` API view.

#     Endpoint: /api/textwallposts/
#     """
#     def test_api_textwallposts_list_endpoint(self):
#         """
#         Ensure we return a text wall post.
#         """
#         response = self.client.get(reverse('textwallposts'))
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(response.data, data)