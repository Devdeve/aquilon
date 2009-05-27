""" Campus is a subclass of Location """
from sqlalchemy import Column, Integer, ForeignKey

from aquilon.aqdb.model import Location, Building
from aquilon.aqdb.column_types.aqstr import AqStr

#TODO: make CDS an inner class.
# Then, in order to create a _cds, call cs.sync() in place of an __init__()
# method for campus, with parameters

class Campus(Location):
    """ Campus is a subtype of location """
    __tablename__ = 'campus'
    __mapper_args__ = {'polymorphic_identity' : 'campus'}
    id = Column(Integer,
                ForeignKey('location.id', name = 'campus_loc_fk',
                           ondelete = 'CASCADE'),
                primary_key=True)


campus = Campus.__table__
campus.primary_key.name = 'campus_pk'
table = campus

class CampusDiffStruct(object):
    """ Handy for populating campuses and finding common parent for
        sublocation structural elements within """

    def __init__(self, dsdb, sess, campus_obj, verbose=0, *args, **kw):
        """ accepts dsdb connection for flexible dependency injection """
        self.dsdb = dsdb
        self.sess = sess
        self.co = campus_obj
        self.verbose = verbose

        building_names = map(lambda x: x[0],
                           dsdb.dump('buildings_by_campus',
                                     campus=self.co.name))

        if len(building_names) < 1:
            msg = "No buildings found for campus '%s'"%(self.co.code)
            raise ValueError(msg)

        q = self.sess.query(Building)
        self.buildings  = q.filter(
            Location.name.in_(building_names)).all()

        self.data = {}
        self.data['cities']     = []
        self.data['countries']  = []
        self.data['continents'] = []

        for b in self.buildings:
            #checking for None here b/c error conditions make that possible
            if b.city is not None:
                self.data['cities'].append(b.city)

            if b.country is not None:
                self.data['countries'].append(b.country)

            #put the is not None into my_set class
            if b.continent is not None:
                self.data['continents'].append(b.continent)

        for k,v in self.data.iteritems():
            self.data[k] = set(v)


    def __repr__(self):
        return '<Campus Struct: name = %s, code = %s, comments = %s >'%(
            self.co.name, self.co.code, self.co.comments)

    def _dbg(self, level, msg):
        if self.verbose >= level:
            print msg

    def _validate(self):
        if len(self.data['continents']) <= 0:
            msg = "No continents found for %s"%(self.co)
            raise ValueError(msg)

        elif len(self.data['countries']) <= 0:
            msg = "No countries found for %s"%(self.co)
            raise ValueError(msg)

        elif len(self.data['cities']) <= 0 :
            msg = "No cities found for campus '%s'"%(self.co)
            raise ValueError(msg)

        elif len(self.data['continents']) > 1:
            #we span continents, raise a BIG alarm!
            #TODO: give error message useful diagnostic info:
            # campus code plus the buildings and continents you found.
            msg = "ERROR: Campus %s with %s. Continents aren't to be spanned"%(
                self.co, self.data['continents'])
            raise ValueError(msg)

    def sync(self):
        self._validate()

        for atrb in ['countries','cities']:
            #if we've hit cities, we can go no farther, so reparent it.
            #logic changes if we need more than one campus per city.
            #this is currently allowable but highly unlikely in dsdb

            if len(self.data[atrb]) > 1 or (
                len(self.data[atrb]) == 1 and atrb == 'cities'):

                self._dbg(3,'Have to reparent %s %s'%(atrb, self.data[atrb]))

                self.data[atrb] = list(self.data[atrb])
                self.co.parent = self.data[atrb][0].parent

                self._dbg(3,'campus parent is now set to %s'%(self.co.parent))

                try:
                    self.sess.add(self.co)
                    self.sess.flush()
                except Exception, e:
                    print 'ERROR commiting new campus parent: %s'%(e)
                    self.sess.close()
                    return False

                for subloc in self.data[atrb]:
                    subloc.parent = self.co
                    msg = '%s parent now set to %s'%(subloc, self.co)
                    self._dbg(3,msg)
                    self.sess.add(subloc)

                self._dbg(3,'commiting changes to sublocs %s'%(self.data[atrb]))

                try:
                    self.sess.commit()
                except Exception, e:
                    print 'rolling back in sync()\n%s'%(e)
                    self.sess.close()
                    return False

                msg = 'new campus %s has sublocs %s'%(self.co,self.co.sublocations)
                self._dbg(3,msg)
                return True

        else:
            #this *should* be caught by _verify() anyway.
            msg = "No valid interpretation for campus %s"%(self.code)
            raise ValueError(msg)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-