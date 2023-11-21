from matplotlib import path
import os

apiPath = os.path.abspath(os.path.join(os.path.abspath(__file__), '../'))

# tables from https://github.com/gmassei/SoilTexture (2021-08-04)

# import tables
def getTable(fname):
    # read file and extract number of classes
    with open(os.path.join(apiPath, fname), 'r') as f:
        x = f.readlines()
    nbClasses = int(x[0])

    # extract reference and definition
    ref = x[1 + nbClasses*4]
    definition = x[-1]

    # extract name of classes
    classNamesRaw = x[1 + nbClasses*4 + 1: 1 + nbClasses*4 + 1 + nbClasses + 1]
    keys = [a.split('=')[0] for a in classNamesRaw]
    vals = [a.split('=')[1].strip() for a in classNamesRaw]
    classNames = dict(zip(keys, vals))

    # extract
    table = {}
    #table['ref'] = ref
    #table['def'] = definition
    for i in range(nbClasses):
        className = x[1 + i*4].strip()
        sandLimits = [float(a) for a in x[3 + i*4].split()]
        clayLimits = [float(a) for a in x[4 + i*4].split()]
        verts = [(a, b) for a, b in zip(sandLimits, clayLimits)]
        table[classNames[className]] = path.Path(verts)

    return table


tables = {
    'USDA': getTable('USDA.dat'),
    'FAO': getTable('FAO.dat'),
    'INTERNATIONAL': getTable('INTERNATIONAL.dat'),
    'ISSS': getTable('ISSS.dat'),
}


def getTexture(sand, clay, classification='USDA'):
    """Provide soil texture given percentage of sand and clay.

    Parameters
    ----------
    sand : float
        Percentage of sand.
    clay : float
        Percentage of clay.
    classification : str, optional
        Classification scheme to use. Choices between 'USDA' (default), 
        'FAO', 'ISSS' or 'INTERNATIONAL'.

    Return
    ------
    texture : str
        Texture as a string.
    """
    table = tables[classification]
    for key in table.keys():
        p = table[key]
        if p.contains_point((sand, clay)) is True:
            return key
    return None


def getTextures(sands, clays, classification='USDA'):
    """Provide soil texture given percentage of sand and clay.

    Parameters
    ----------
    sands : list of float
        Percentages of sand.
    clays : list of float
        Percentages of clay.
    classification : str, optional
        Classification scheme to use. Choices between 'USDA' (default), 
        'FAO', 'ISSS' or 'INTERNATIONAL'.

    Return
    ------
    texture : str
        Texture as a string.
    """
    table = tables[classification]
    keys = [None]*len(sands)
    for i in range(len(sands)):
        sand = sands[i]
        clay = clays[i]
        for key in table.keys():
            p = table[key]
            if p.contains_point((sand, clay)) is True:
                keys[i] = key
                break
    return keys

# text
#getTexture(23, 12, classification='FAO')
#getTextures([13, 45], [50, 24], classification='FAO')