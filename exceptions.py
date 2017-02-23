# FFmpeg


class FFmpegBinaryNotFound(FileNotFoundError):
    pass


class FFmpegProcessException(Exception):
    pass


class FFmpegInputNotFoundException(FileNotFoundError):
    pass


class FFmpegOutputAlreadyExistsException(FileExistsError):
    pass

# FFprobe


class FFprobeBinaryNotFound(FileNotFoundError):
    pass


class FFprobeProcessException(Exception):
    pass


class FFprobeTerminatedException(Exception):
    pass

# FFprobeMetadataFilter


class UnknownFilterSelector(ValueError):
    pass


class UnknownMetadataParameter(KeyError):
    pass


class WrongConditionType(TypeError):
    pass


class UnknownOperator(ValueError):
    pass


class ConditionPairProcessingException(Exception):

    def __init__(self, value_left, operator, value_right, *args, **kwargs):
        msg = 'value_left: {} of type {}, operator: {}, value_right {} of type {}'.format(
            value_left, type(value_left), operator, value_right, type(value_right)
        )
        super().__init__(msg, *args, **kwargs)


class UnknownStreamType(ValueError):
    pass


class StreamIndexOutOfRange(ValueError):
    pass
