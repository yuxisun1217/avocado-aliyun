
class SkipCase(Exception):
    def __init__(self, err="Skip this case."):
        Exception.__init__(self, err)


class VMStatusError(Exception):
    def __init__(self, err="VM status is wrong."):
        Exception.__init__(self, err)


class VMConnectError(Exception):
    def __init__(self, err="VM connection error"):
        Exception.__init__(self, err)

