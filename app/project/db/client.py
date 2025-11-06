from .system import System

class DBClient(object):

    def __init__(
        self,
        mysql, # SQL Connection object
        config: dict
    ) -> None:

        # set database link
        self.mysql = mysql

        # init the Classes
        self.system = System(self)
