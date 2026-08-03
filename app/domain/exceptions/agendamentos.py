from domainException import DomainException

class AgendamentoNotFoundException(DomainException):
    """Exception raised when an agendamento is not found."""
    pass

class AgendamentoAlreadyExistsException(DomainException):
    """Exception raised when an agendamento already exists."""
    pass

class InvalidAgendamentoStatusException(DomainException):
    """Exception raised when an agendamento has an invalid status."""
    pass

class InvalidAgendamentoTimeException(DomainException):
    """Exception raised when an agendamento has an invalid time."""
    pass

class AgendamentoConflictException(DomainException):
    """Exception raised when an agendamento conflicts with another agendamento."""
    pass