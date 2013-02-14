import re
from mca.model.meta import engine
from utils import timestamp2ReadableString
import traceback
from shapely.wkt import loads

import sys
from osgeo import osr

def esriprj2standards(shapeprj_path):
    try:
        prj_file = open(shapeprj_path, 'r')
        prj_txt = prj_file.read()
        srs = osr.SpatialReference()
        srs.ImportFromESRI([prj_txt])
        srs.ExportToWkt()
        srs.ExportToProj4()
        srs.AutoIdentifyEPSG()
        return srs.GetAuthorityCode(None) # returns None if no epsg found
    except:
        return None

def getShapelyNodes(name):
    nodes = engine.execute("SELECT node_id, ST_AsText(geom) FROM %s.node" %name)
    for n in nodes:
        yield (n[0], loads(n[1]))

allSrs = []
def getAllSrs():
    if not(allSrs):
        res = engine.execute('select auth_srid, srtext from spatial_ref_sys')
        for current in res:
            if current[1].startswith('PROJCS["'):
                allSrs.append('[%s] %s' %(current[0], re.search(r'PROJCS\["(.*)",GEOGCS\[".*', current[1]).group(1)))
            elif current[1].startswith('GEOGCS["'):
                allSrs.append('[%s] %s' %(current[0], re.search(r'GEOGCS\["(.*)",DATUM\[".*', current[1]).group(1)))
    return allSrs


def cleanPublicSchema(name):
    connection = engine.connect()
    trans = connection.begin()
    try:
        connection.execute("DROP TABLE public.%s" %name)
        trans.commit()
    except:
        trans.rollback()
        print traceback.print_exc()
    finally:
        connection.close()


def deleteTopology(name):
    connection = engine.connect()
    trans = connection.begin()
    try:
        # delete meta
        connection.execute("delete from topology.meta where topology_id in (select id from topology.topology where name = '%s')" %name)
        # drop topology
        connection.execute("select topology.DropTopology('%s')" %name)
        trans.commit()
    except:
        trans.rollback()
        print traceback.print_exc()
    finally:
        connection.close()


def topologyExists(name):
    sql = "select id from topology.topology where name = '%s'" %name
    res = engine.execute(sql)
    return res.fetchone() is not None


def getAllProjects():
    projects = engine.execute('select name, srid, author, creation, snapping, kind, grid_resolution from topology.topology, topology.meta where topology.topology.id = topology.meta.topology_id')
    for proj in projects:
        projName = str(proj[0])
        snapping = proj[4] if proj[4] else ''
        resolution = proj[6] if proj[6] else ''
        sql = 'select edge, node from (select count(edge_id) as edge from %s.edge_data) as xxx, (select count(node_id) as node from %s.node) as yyy'
        res = engine.execute(sql %(projName, projName))
        for r in res:
            yield (proj[5], projName, proj[1], r[0], r[1], snapping, resolution, proj[2], timestamp2ReadableString(proj[3]))


degreeUnit = 'degree (lon/lat)'
def getUnit(srs):
    conn = engine.connect()
    trans = conn.begin()
    try:
        sql = 'SELECT proj4text FROM public.spatial_ref_sys '
        sql += 'WHERE auth_srid = %s' %srs
        res = conn.execute(sql)
        proj4text = res.fetchone()
        unit = re.search(r'.*units=(.*)\s\+.*', proj4text[0])
        if unit is not None:
            return unit.group(1)
        else:
            return degreeUnit
    except:
        print traceback.print_exc()
    finally:
        conn.close()


def clean_db():
    try:
        sql = "SELECT table_name"
        sql += " FROM INFORMATION_SCHEMA.TABLES"
        sql += " WHERE table_schema = 'public'"
        sql += " AND table_type = 'BASE TABLE'"
        res = engine.execute(sql)
        for r in res:
            name = str(r[0])
            if name != 'spatial_ref_sys':
                drop = 'DROP TABLE public.%s' %name
                engine.execute(drop)
    except:
        print traceback.print_exc()

