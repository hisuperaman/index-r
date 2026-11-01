from rest_framework import status
from rest_framework.exceptions import APIException


class AnswerUnavailable(APIException):
	status_code = status.HTTP_503_SERVICE_UNAVAILABLE
	default_detail = "Something went wrong while generating the answer. Please try again."
	default_code = 'answer_unavailable'
