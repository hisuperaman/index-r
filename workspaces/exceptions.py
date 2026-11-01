from rest_framework import status
from rest_framework.exceptions import APIException


class AnswerUnavailable(APIException):
	status_code = status.HTTP_503_SERVICE_UNAVAILABLE
	default_detail = "The question was saved, but an answer could not be written. Try again shortly."
	default_code = 'answer_unavailable'
