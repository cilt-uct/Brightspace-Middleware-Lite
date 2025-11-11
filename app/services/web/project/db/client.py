from .logs import Logs
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
        self.logs = Logs(self)
        self.system = System(self)
