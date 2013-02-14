import os
from mca import basedir
import ConfigParser

config = None

class Config:
    def __init__(self):
        home    = os.path.expanduser('~')
        staterc = os.path.join(home, '.mca.config')
        state   = ConfigParser.RawConfigParser()
        dirty   = False

        print 'using config: ', staterc

        self.lastdir = 'lastdir'
        self.loaddir = 'load'
        self.computedir = 'compute'

        if os.path.exists(staterc):
            state.read(staterc)
        else:
            dirty = True

        if not state.has_section(self.lastdir):
            state.add_section(self.lastdir)
            dirty = True

        if not state.has_option(self.lastdir, self.loaddir) or not os.path.isdir(state.get(self.lastdir, self.loaddir)):
            state.set(self.lastdir, self.loaddir, home)
            dirty = True

        if not state.has_option(self.lastdir, self.computedir) or not os.path.isdir(state.get(self.lastdir, self.computedir)):
            state.set(self.lastdir, self.computedir, home)
            dirty = True

        self.__home     = home
        self.__staterc  = staterc
        self.__state    = state
        self.__dirty    = dirty

        self.save()

    def __setLastDir(self, opt, val):
        if os.path.isdir(val):
            if not (val == self.__state.get(self.lastdir, opt)):
                self.__dirty = True

            self.__state.set(self.lastdir, opt, val)

    def __getLastDir(self, opt):
        if self.__state.has_option(self.lastdir, opt):
            return self.__state.get(self.lastdir, opt)
        return None

    def setLoadDir(self, val):
        self.__setLastDir(self.loaddir, val)

    def getLoadDir(self):
        return self.__getLastDir(self.loaddir)

    def setComputeDir(self, val):
        self.__setLastDir(self.computedir, val)

    def getComputeDir(self):
        return self.__getLastDir(self.computedir)

    def save(self):
        if self.__dirty:
            with open(self.__staterc, 'w') as stateFile:
                print 'saving state: ', self.__staterc
                self.__state.write(stateFile)
            self.__dirty = False
