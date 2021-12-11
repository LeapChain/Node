from django.core.exceptions import ValidationError as DjangoValidationError
from pydantic import ValidationError as PydanticValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError


def convert_to_drf_validation_error(exception: PydanticValidationError):
    errors = {}
    for error in exception.errors():
        loc = error['loc']
        key = 'non_field_errors' if loc == ('__root__',) else '.'.join(map(str, loc))
        errors[key] = [error['msg']]

    return DRFValidationError(errors)


class ValidationError(DjangoValidationError):
    pass


class NotEnoughNestingError(ValueError):
    pass
