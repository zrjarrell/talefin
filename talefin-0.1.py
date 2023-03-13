import pandas as pd
import re
import math
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
import os


#testdata
pathToMummichogOutput = "/Users/zrj/Desktop/talefin/test-data/cd-xi-f_adef_lung_c18neg_limma2way-pls/1677524736.87.2way-outer-join-fdr20/tsv/mcg_pathwayanalysis_2way-outer-join-fdr20.xlsx"

pathToMummichogInput = "/Users/zrj/Desktop/talefin/test-data/cd-xi-f_adef_lung_c18neg_limma2way-pls/formummichog-outer-join-2way-sigresults-fdr20.txt"

pathToFeatureTable = "/Users/zrj/Desktop/talefin/test-data/cd-xi-f_adef_lung_c18neg_featuretable.txt"

pathToClasslist = "/Users/zrj/Desktop/talefin/test-data/cd-xi-f_adef_lung_classlist.txt"

outputPath = "./output1"

#testdata2
pathToMummichogOutput = "/Users/zrj/Desktop/talefin/test-data-2/cd-xi_males_testes_hilicpos_limma-pls/1648495652.23.hilicpos_p05vip2/tsv/mcg_pathwayanalysis_hilicpos_p05vip2.xlsx"

pathToMummichogInput = "/Users/zrj/Desktop/talefin/test-data-2/cd-xi_males_testes_hilicpos_limma-pls/hilicpos_formummichog.txt"

pathToFeatureTable = "/Users/zrj/Desktop/talefin/test-data-2/cd-xi_males_testes_hilicpos_featuretable.txt"

pathToClasslist = "/Users/zrj/Desktop/talefin/test-data-2/cd-xi_males_testes_classlist.txt"

outputPath = "./output2"


mummichogSelectedFeatureThreshold = 0.05
mummichogSignificanceThreshold = 0.05
mummichogMinimumOverlap = 4


################################################################

class Pathway:
    def __init__(self, sigPathways, pathwayIndex):
        self.name = sigPathways.iloc[pathwayIndex, 0]
        self.overlapSize = sigPathways.iloc[pathwayIndex, 1]
        self.pathwaySize = sigPathways.iloc[pathwayIndex, 2]
        self.pValue = sigPathways.iloc[pathwayIndex, 4]
        self.metabolites = list(set(sigPathways.iloc[pathwayIndex, 5].split('$')))
        self.keggIDs = list(set(sigPathways.iloc[pathwayIndex, 6].split(';')))
        self.mzs = list(set(re.split(';|,', sigPathways.iloc[pathwayIndex, 7])))
    
    def printInfo(self):
        print(self.name + " - (" + str(self.overlapSize) + "/" + str(self.pathwaySize) + ")")
        print("p-value: " + str(self.pValue))
        print("KEGG IDs: " + str(self.keggIDs))

class KEGGNodes:
    def __init__(self, keggID, path, annotations):
        features = annotations[annotations['id']==keggID]
        self.id = keggID
        self.mzs = features.iloc[:,-2].tolist()
        self.times = features.iloc[:,-1].tolist()
        self.adducts = features.iloc[:,2].tolist()
        self.pvalues = []
        self.tstatistics = []
        self.pathways = [path]
        self.pathwayNames = [path.name]
        self.sigFeatures = []
    
    def addPathway(self, newPathway):
        self.pathways = self.pathways + [newPathway]
        self.pathwayNames += [newPathway.name]
    
    def addTimesStats(self, inputList):
        for i in range(0, len(self.mzs)):
            matches = inputList[(inputList['roundMZ']==self.mzs[i]) & (inputList['roundTime']==self.times[i])]
            matches.drop_duplicates()
            if len(matches) == 1:
                self.pvalues += [matches.iloc[0, 2]]
                self.tstatistics += [matches.iloc[0, 3]]
            else:
                self.pvalues += matches.iloc[:, 2].tolist()
                self.tstatistics += matches.iloc[:, 3].tolist()
    
    def printInfo(self):
        print(self.id + ": ")
        print(', '.join(self.pathwayNames))
        print('\nm/z: ' + str(self.mzs))
        print('times: ' + str(self.times))
        print('adducts: ' + str(self.adducts))
        print('p-values: ' + str(self.pvalues))
        print('t-statistics: ' + str(self.tstatistics))

class featureNode:
    def __init__(self, unique, uniqueList):
        self.label = str(uniqueList.iloc[unique, 1]) + '_' + str(uniqueList.iloc[unique, 2])
        self.mz = uniqueList.iloc[unique, 1]
        self.time = uniqueList.iloc[unique, 2]
        self.keggMatches = []

def splitMummichogOutput(path, overlapMin, pvalueMax):
    wholeOutput = pd.read_excel(path)
    splitIndex = wholeOutput[wholeOutput['pathway']=="Annotation for metabolites in significant pathways"].index[0]
    pathwayResults = wholeOutput.iloc[:(splitIndex - 1), :]
    bigPathways = pathwayResults[pathwayResults['overlap_size'] >= overlapMin]
    sigPathways = bigPathways[bigPathways['p-value'] < pvalueMax].reset_index(drop=True)
    annotations = wholeOutput.iloc[(splitIndex + 1):, :6]
    annotations.columns = annotations.iloc[0, :]
    annotations = annotations.iloc[1:,].reset_index(drop=True)
    return sigPathways, annotations

def truncate(n, decimals=0):
    expoN = n * 10 ** decimals
    if abs(expoN * 10) % 10 == 5:
        return math.floor(expoN)/ 10 ** decimals
    else:
        return properRound(n, decimals)

def properRound(n, decimals=0):
    expoN = n * 10 ** decimals
    if abs(expoN) - abs(math.floor(expoN)) < 0.5:
        result =  math.floor(expoN) / 10 ** decimals
    else:
        result = math.ceil(expoN) / 10 ** decimals
    if decimals <= 0:
        return int(result)
    return result

def floorRound(n, decimals=0):
    expoN = n * 10 ** decimals
    result = math.floor(expoN) / 10 ** decimals
    if decimals <= 0:
        return int(result)
    return result

def ceilRound(n, decimals=0):
    expoN = n * 10 ** decimals
    result = math.ceil(expoN) / 10 ** decimals
    if decimals <= 0:
        return int(result)
    return result

def floorCeilRoundInputs(inputList, MZdecimal=4, timeDecimal=0):
    floorMZs = []
    ceilMZs = []
    roundMZs = []
    floorTimes = []
    ceilTimes = []
    roundTimes = []
    for i in inputList.index:
        floorMZs += [floorRound(inputList.loc[i, 'mz'], MZdecimal)]
        ceilMZs += [ceilRound(inputList.loc[i, 'mz'], MZdecimal)]
        roundMZs += [properRound(inputList.loc[i, 'mz'], MZdecimal)]
        floorTimes += [floorRound(inputList.loc[i, 'time'], timeDecimal)]
        ceilTimes += [ceilRound(inputList.loc[i, 'time'], timeDecimal)]
        roundTimes += [properRound(inputList.loc[i, 'time'], timeDecimal)]
    inputList['floorMZ'] = floorMZs
    inputList['ceilMZ'] = ceilMZs
    inputList['roundMZ'] = roundMZs
    inputList['floorTime'] = floorTimes
    inputList['ceilTime'] = ceilTimes
    inputList['roundTime'] = roundTimes
    return inputList

def fixOutputRounding(annotations, inputList):
    newAnnotations = pd.DataFrame(columns=annotations.columns)
    newAnnotations['mz'] = ''
    newAnnotations['time'] = ''
    for row in annotations.index:
        matches = inputList[inputList['roundMZ']==annotations.iloc[row, 0]]
        if len(matches) < 1:
            matches = inputList[(inputList['floorMZ'] == annotations.iloc[row, 0]) | (inputList['ceilMZ'] == annotations.iloc[row, 0])]
        matches = matches.drop_duplicates()
        for match in matches.index: 
            rowData = annotations.iloc[row, :]
            rowData['mz'] = matches.loc[match,'roundMZ']
            rowData['time'] =  matches.loc[match, 'roundTime']
            newAnnotations.loc[len(newAnnotations)] = rowData
    return newAnnotations

def fixFeatureTableRounding(featureTable, inputList, MZdecimal=4, timeDecimal=0):
    newFeatureTable = pd.DataFrame(columns=featureTable.columns)
    newFeatureTable['roundMZ'] = ''
    newFeatureTable['roundTime'] = ''
    for feature in featureTable.index:
        roundMZ = properRound(featureTable.loc[feature, :]['mz'], MZdecimal)
        roundTime = properRound(featureTable.loc[feature, :]['time'], timeDecimal)
        matches = inputList[(inputList['roundMZ']==roundMZ) & (inputList['roundTime']==roundTime)]
        if len(matches) < 1:
            floorMZ = floorRound(featureTable.loc[feature, :]['mz'], MZdecimal)
            floorTime = floorRound(featureTable.loc[feature, :]['time'], timeDecimal)
            ceilMZ = ceilRound(featureTable.loc[feature, :]['mz'], MZdecimal)
            ceilTime = ceilRound(featureTable.loc[feature, :]['time'], timeDecimal)
            matches = inputList[((inputList['roundMZ']==floorMZ) & (inputList['roundTime']==floorTime)) |
                                ((inputList['roundMZ']==floorMZ) & (inputList['roundTime']==ceilTime)) |
                                ((inputList['roundMZ']==ceilMZ) & (inputList['roundTime']==floorTime)) |
                                ((inputList['roundMZ']==ceilMZ) & (inputList['roundTime']==ceilTime))]
        matches = matches.drop_duplicates()
        for match in matches.index:
            rowData = featureTable.iloc[feature, :]
            rowData['roundMZ'] = matches.loc[match, 'roundMZ']
            rowData['roundTime'] = matches.loc[match, 'roundTime']
            newFeatureTable.loc[len(newFeatureTable)] = rowData
    if timeDecimal <= 0:
        newFeatureTable['roundTime'] = newFeatureTable['roundTime'].astype(int)
    return newFeatureTable

def buildPathways(sigPathways):
    pathways = []
    for path in sigPathways.index:
        pathways += [Pathway(sigPathways, path)]
    return pathways

def buildKEGGNodes(pathways, annotations, inputList):
    allKEGGIDs = {}
    for path in pathways:
        for keggID in path.keggIDs:
            if keggID in allKEGGIDs:
                allKEGGIDs[keggID].addPathway(path)
            else:
                allKEGGIDs[keggID] = KEGGNodes(keggID, path, annotations)
    for keggID in allKEGGIDs:
        allKEGGIDs[keggID].addTimesStats(inputList)
    return allKEGGIDs

def buildUniqueFeatures(fullList):
    uniqueFeatures = {}
    uniqueList = fullList.drop_duplicates(subset=['mz', 'time']).reset_index(drop=True)
    for unique in uniqueList.index:
        uniqueFeatures[str(uniqueList.iloc[unique, 1]) + '_' + str(uniqueList.iloc[unique, 2])] = featureNode(unique, uniqueList)
    for row in fullList.index:
        uniqueFeatures[str(fullList.iloc[row, 1]) + '_' + str(fullList.iloc[row, 2])].keggMatches += [fullList.iloc[row, 0]]
    return uniqueFeatures, uniqueList

def compileFeatureData(features, nodes, threshold, classes):
    df = pd.DataFrame(columns= ['id', 'mz', 'time'])
    d = 0
    for node in nodes:
        c = 0
        for pvalue in nodes[node].pvalues:
            if pvalue < threshold:
                df.loc[d] = [nodes[node].id, nodes[node].mzs[c], nodes[node].times[c]]
                d += 1
            c += 1
    uniqueFeatures, uniqueList = buildUniqueFeatures(df)
    features = features.iloc[:, 2:].rename(columns={'roundMZ': 'mz', 'roundTime': 'time'})
    df = uniqueList.merge(features, how='inner', on=['mz','time'])
    for feature in uniqueFeatures:
        featureData = df[(df['mz']== uniqueFeatures[feature].mz) & (df['time']== uniqueFeatures[feature].time)]
        featureData = featureData.iloc[:, 3:].T
        featureData = classes.join(featureData)
        featureData.columns = ['class', 'intensity']
        uniqueFeatures[feature].intensityTable = featureData
    return uniqueFeatures

def mapFeaturesToKEGG(featureDict, keggDict):
    for feature in featureDict:
        for keggID in featureDict[feature].keggMatches:
            keggDict[keggID].sigFeatures += [feature]

def createGraphs(featureDict):
    graphDir = os.path.join('./graphs')
    os.mkdir(graphDir)
    for feature in featureDict:
        graph = sns.boxplot(x='class', y='intensity', data=featureDict[feature].intensityTable)
        graph = sns.stripplot(x='class', y='intensity', data=featureDict[feature].intensityTable, color='orange', jitter=0.2, size=2.5)
        plt.title(featureDict[feature].label)
        filePath = os.path.join(graphDir, featureDict[feature].label + '.pdf')
        plt.savefig(filePath)
        plt.clf()
        featureDict[feature].filePath = filePath

def reducePathwayCards(pathways, keggNodes, selectionThreshold):
    for pathway in pathways:
        pathway.reducedNodesLabels = []
        pathway.reducedNodesKeys = []
        for newID in pathway.keggIDs:
            repeated = False
            c = 0
            for oldID in pathway.reducedNodesKeys:
                if sorted(keggNodes[oldID].mzs) == sorted(keggNodes[newID].mzs) and sorted(keggNodes[oldID].times) == sorted(keggNodes[newID].times) and sorted(keggNodes[oldID].adducts) == sorted(keggNodes[newID].adducts):
                    repeated = True
                    pathway.reducedNodesLabels[c] += (', ' + newID)
                c += 1
            if not repeated:
                pathway.reducedNodesLabels += [newID]
                pathway.reducedNodesKeys += [newID]

def writeKEGGcard(keggID, keggDict, featureDict, pathway, c, threshold):
    keggCard = """<div class="keggCard">
        <p><b>%s</b></p>
        <div class="graphContainer">
    """%(pathway.reducedNodesLabels[c])
    for feature in keggDict[keggID].sigFeatures:
        keggCard += """<img src="%s" width="450">"""%(featureDict[feature].filePath)
    keggCard += """</div>
    <table>
        <tr>
            <th><i>m/z</i></th>
            <th>Time</th>
            <th>Adduct</th>
            <th>p-value</th>
            <th>t-statistic</th>
        </tr>"""
    d = 0
    for feature in keggDict[keggID].mzs:
        if keggDict[keggID].pvalues[d] < threshold:
            keggCard += """<tr class="significant">"""
        else:
            keggCard += """<tr>"""
        keggCard += """<td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
                <td>%s</td>
            </tr>"""%(str(round(feature, 4)), str(int(round(keggDict[keggID].times[d], 0))), keggDict[keggID].adducts[d], str(round(keggDict[keggID].pvalues[d], 6)), keggDict[keggID].tstatistics[d])
        d += 1
    keggCard += "</table>"
    keggCard += "</div>"
    return keggCard

def writePathwayBlock(pathway, keggDict, featureDict, threshold):
    pathwayTitleButton = """
    <button type="button" class="pathwayButton">
        <div class="pathwayLabel">
            <div class="pathwayName"><b>%s</b></div>
            <div class="pathwaySignificance"><b>%s</b></div>
        </div>
        <div class="keggLink"><a href=""><b>View Kegg Map</b></a></div>
    </button>"""%(pathway.name + " - (" + str(pathway.overlapSize) + "/" + str(pathway.pathwaySize) + ")", "p-value: " + str(round(pathway.pValue, 8)))
    pathwayContainer = """<div class="pathwayContainer">"""
    c = 0
    for keggID in pathway.reducedNodesKeys:
        pathwayContainer += writeKEGGcard(keggID, keggDict, featureDict, pathway, c, threshold)
        c += 1
    pathwayContainer += """</div>"""
    return pathwayTitleButton + pathwayContainer

def generateHTMLreport(pathways, mummichogOutput, pathwayThreshold, featureThreshold, keggDict, featureDict, selectionThreshold):
    report = open('report.html', 'w')
    heading = """<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>TaleFin Report</title>
        <link href="style.css" rel="stylesheet">
    </head>
    <body>
    <div class="heading">
        <h2><b>TaleFin Report</b></h2>
        <p><b>Report for mummichog output:</b> %s</p>
        <p><b>Date:</b> %s</p>
        <p><b>Pathway significance threshold:</b> %s</p>
        <p><b>Required selected features:</b> %s</p>
    </div>
    """%(os.path.basename(mummichogOutput), str(datetime.now()), pathwayThreshold, featureThreshold)
    report.write(heading)
    for pathway in pathways:
        pathwayDiv = writePathwayBlock(pathway, keggDict, featureDict, selectionThreshold)
        report.write(pathwayDiv)
    footing = """<script>
    var pathwayButton = document.getElementsByClassName("pathwayButton");
    var i;
    
    for (i = 0; i < pathwayButton.length; i++) {
        pathwayButton[i].addEventListener("click", function() {
            this.classList.toggle("active");
            var content = this.nextElementSibling;
            if (content.style.display === "flex") {
                content.style.display = "none";
            } else {
                content.style.display = "flex";
            }
        });
    }
    </script>
    </body>
    </html>"""
    report.write(footing)
    report.close()

def generateStylesheet():
    stylesheet = open('style.css', 'w')
    styles = """
        * {
    font-family: Arial;
}

.heading {
    margin: 40px 10px 0;
}
h2, p {
    padding: 4px;
}

.pathwayButton {
    padding: 16px;
    width: 100%;
    margin: 2px 0 0 0;
    border: none;
    text-align: left;
    outline: none;
    font-size: 15px;
    cursor: pointer;
    background-color: rgb(208, 182, 254);
    color: #111;
    display: flex;
    justify-content: space-between;
    border-radius: 8px;
}

.active, .pathwayButton:hover {
    background-color: rgb(171, 122, 255);
}

.pathwayLabel {
    display: flex;
    justify-content: space-between;
    width: 90%;
}

.keggLink {
    width: 10%;
    min-width: 9em;
    text-align: right;
}

.pathwayContainer {
    display: none;
    padding: 16px;
    font-size: 90%;
    gap: 10px;
    flex-wrap: wrap;
}

.keggCard {
    min-width: 475px;
    flex-grow: 1;
    background-color: rgb(181, 226, 254);
    display: flex;
    flex-direction: column;
    align-items: center;
    border-radius: 8px;
}

.graphContainer {
    width: 450px;
    height: 345px;
    overflow-y: scroll;
    overflow-x: hidden;
}

table {
    border-collapse: collapse;
    margin: 8px;
}

th, td {
    border: 1px solid rgb(117, 201, 254);
    padding: 0.5em;
    text-align: left;
}

th {
    background-color: rgb(197, 233, 255);
}

td {
    background-color: rgb(211, 238, 255);
}

.significant {
    color: rgb(160, 0, 0);
    font-weight: bold;
}
    """
    stylesheet.write(styles)
    stylesheet.close()


os.mkdir(outputPath)
os.chdir(outputPath)
mummichogInput = pd.read_table(pathToMummichogInput, sep="\t")
classes = pd.read_table(pathToClasslist, sep="\t", index_col = 0)
features = pd.read_table(pathToFeatureTable, sep="\t")
mummichogInput = floorCeilRoundInputs(mummichogInput, 4)

sigPathwayTable, annotationsTable = splitMummichogOutput(pathToMummichogOutput, mummichogMinimumOverlap, mummichogSignificanceThreshold)
pathways = buildPathways(sigPathwayTable)

annotationsTable = fixOutputRounding(annotationsTable, mummichogInput)
features = fixFeatureTableRounding(features, mummichogInput)

allIDs = buildKEGGNodes(pathways, annotationsTable, mummichogInput)

featureDict = compileFeatureData(features, allIDs, mummichogSelectedFeatureThreshold, classes)
mapFeaturesToKEGG(featureDict, allIDs)

createGraphs(featureDict)

reducePathwayCards(pathways, allIDs, mummichogSelectedFeatureThreshold)

generateHTMLreport(pathways, pathToMummichogOutput, mummichogSignificanceThreshold, mummichogMinimumOverlap, allIDs, featureDict, mummichogSelectedFeatureThreshold)
generateStylesheet()

