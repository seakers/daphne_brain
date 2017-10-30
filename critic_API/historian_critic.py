import csv
import json
import numpy as np
from sqlalchemy.orm import sessionmaker

import histdb_API.models as models


class Critic:
    
    def __init__(self):

        # Connect to the CEOS database
        engine = models.db_connect()
        self.session = sessionmaker(bind=engine)()

        self.orbitsDataset = [
            {"name": "LEO-600-polar-NA", "type": "Inclined, non-sun-synchronous","altitude": 600,"LST":""},
            {"name": "SSO-600-SSO-AM", "type": "Sun-synchronous", "altitude": 600, "LST": "AM"},
            {"name": "SSO-600-SSO-DD", "type": "Sun-synchronous", "altitude": 600, "LST": "DD"},
            {"name": "SSO-800-SSO-DD", "type": "Sun-synchronous", "altitude": 800, "LST": "DD"},
            {"name": "SSO-800-SSO-PM", "type": "Sun-synchronous", "altitude": 800, "LST": "PM"}]

        self.instrumentsDataset = [
            {"name": "ACE_ORCA", "type": "Ocean colour instruments", "technology": "Medium-resolution spectro-radiometer", "geometry": "Cross-track scanning", "wavebands": ["UV","VIS","NIR","SWIR"]},
            {"name": "ACE_POL", "type": "Multiple direction/polarisation radiometers", "technology": "Multi-channel/direction/polarisation radiometer", "geometry": "ANY", "wavebands": ["VIS","NIR","SWIR"]},
            {"name": "ACE_LID", "type": "Lidars", "technology": "Atmospheric lidar", "geometry": "Nadir-viewing", "wavebands": ["VIS","NIR"]},
            {"name": "CLAR_ERB", "type": "Hyperspectral imagers", "technology": "Multi-purpose imaging Vis/IR radiometer", "geometry": "Nadir-viewing", "wavebands": ["VIS","NIR","SWIR","TIR","FIR"]},
            {"name": "ACE_CPR", "type": "Cloud profile and rain radars", "technology": "Cloud and precipitation radar", "geometry": "Nadir-viewing", "wavebands": ["MW"]},
            {"name": "DESD_SAR", "type": "Imaging microwave radars", "technology": "Imaging radar (SAR)", "geometry": "Side-looking", "wavebands": ["MW","L-Band","S-Band"]},
            {"name": "DESD_LID", "type": "Lidars", "technology": "Lidar altimeter", "geometry": "ANY", "wavebands": ["NIR"]},
            {"name": "GACM_VIS", "type": "Atmospheric chemistry", "technology": "High-resolution nadir-scanning IR spectrometer", "geometry": "Nadir-viewing", "wavebands": ["UV","VIS"]},
            {"name": "GACM_SWIR", "type": "Atmospheric chemistry", "technology": "High-resolution nadir-scanning IR spectrometer", "geometry": "Nadir-viewing", "wavebands": ["SWIR"]},
            {"name": "HYSP_TIR", "type": "Imaging multi-spectral radiometers (vis/IR)", "technology": "Medium-resolution IR spectrometer", "geometry": "Whisk-broom scanning", "wavebands": ["MWIR", "TIR"]},
            {"name": "POSTEPS_IRS", "type": "Atmospheric temperature and humidity sounders", "technology": "Medium-resolution IR spectrometer", "geometry": "Cross-track scanning", "wavebands": ["MWIR", "TIR"]},
            {"name": "CNES_KaRIN", "type": "Radar altimeters", "technology": "Radar altimeter", "geometry": "Nadir-viewing", "wavebands": ["MW", "Ku-Band"]}]

        self.norb = len(self.orbitsDataset)
        self.ninstr = len(self.instrumentsDataset)
        
        
        
        
    def criticizeArchitecture(self, archInput):
        
        result = []
        
        # Check if each instrument had flown in the similar orbit before
        n = 0
        for o in range(self.norb):
            for i in range(self.ninstr):
                
                if archInput[n]:
                    
                    orbit = self.orbitsDataset[o]
                    instrument = self.instrumentsDataset[i]
                
                    res = self.getSimilarInstruments(orbit, instrument)
                    
                    if len(res) == 0:
                        result.append([
                            "historian1",
                            "Instrument %s has never been flown in orbit %s before" % \
                                 (instrument["alias"], orbit["alias"])
                        ])
                    else:
                        result.append([
                            "historian1",
                            "Instrument %s has been flown in orbit %s before (%s matches in the database)" % \
                                (instrument["alias"], orbit["alias"], len(res)),
                            str(', '.join([r.name for r in res]))
                    ])
            
            n+=1
        
        

        # Check if similar missions can be found
        missionsDatabase = self.session.query(models.Mission)
        
        for o in range(self.norb):
            
            orbit = self.orbitsDataset[o]
            
            instruments = []
            for i in range(self.ninstr):
                if archInput[self.ninstr*o+i]:
                    instruments.append(self.instrumentsDataset[i])
                
            
            res = self.missionsSimilarity(orbit, instruments, missionsDatabase)
            
            if len(instruments) > 0:
                if res[0] < 6:
                    result.append([
                        "historian2",
                        "Your mission is odd: There are no similar missions to %s in orbit %s in the database. Consider changing it" % \
                            (str([i["alias"] for i in instruments]), orbit["alias"])
                    ])
                else:
                    result.append([
                        "historian2",
                        "The most similar mission to %s in orbit %s is %s (score: %.2f/10)" % \
                            (str([i["alias"] for i in instruments]), orbit["alias"], res[1].name, res[0]),
                        '<br>'.join(["Instrument similar to %s (score: %.2f)" % \
                            (i[0], i[2]) for i in self.instrumentsMatchDataset(res[1].instruments)])
                    ])
                    
      
                    
#        # Analyst
#        if len(''.join(archInput)) > 0:
#            res = self.matchFeatures(archInput)
#            if len(res) == 0:
#                result.append([
#                    "analyst",
#                    "Your design doesn't have much in common with other good designs"
#                ])
#            else:
#                result.append([
#                    "analyst",
#                    "Your design seems to have %d common features among good desings" % len(res),
#                    '<br>'.join(["Features: %s" % r for r in res])
#                ])
#                
#                
                
                
                
#                
#        # Explorer
#        if len(''.join(archInput)) > 0:
#            res = self.matchSimilar(archInput)
#            if len(res) == 0:
#                result.append([
#                    "explorer",
#                    "I tried a few changes and couldn't find an easy way to improve your design"
#                ])
#            else:
#                result.append([
#                    "explorer",
#                    "I have found %d designs that are similar to yours but a little better " % len(res),
#                    '<br>'.join(["Designs: %s (Science: %.2f, Cost: %.2f)" % (r[0], r[1], r[2]) for r in res])
#                ])



        # Return result
        return result
        
        
        
        
        
        
        
        
        
        
        
        
    # Used to compute CRITIC1.csv
    def getSimilarInstruments(self, orbit, instrument):
        # Get instruments with similar characteristics and similar orbits
        query = self.session.query(models.Instrument) \
            .filter(models.Instrument.types.any(models.InstrumentType.name == instrument["type"])) \
            .filter(models.Instrument.technology == instrument["technology"]) \
            .filter(models.Instrument.geometries.any(models.GeometryType.name == instrument["geometry"])) \
            .filter(models.Instrument.wavebands.any(models.Waveband.name.in_(instrument["wavebands"]))) \
            .filter(models.Instrument.missions.any( \
                models.Mission.orbit_type == orbit["type"])) \
            .filter(models.Instrument.missions.any( \
                models.Mission.orbit_altitude.between(orbit["altitude"]-50, orbit["altitude"]+50))) \
            .filter(models.Instrument.missions.any( \
                models.Mission.orbit_LST == orbit["LST"]))
        # Return result
        result = query.all()
        return result

    
    
    # Used to compute CRITIC2.csv
    def orbitsSimilarity(self, orbit1, mission2):
        score = 0
        # Score orbit type
        if orbit1["type"] == mission2.orbit_type:
            score += 1
        # Score orbit altitude
        if orbit1["altitude"]-50 < mission2.orbit_altitude < orbit1["altitude"]+50:
            score += 1
        # Score orbit LST
        if orbit1["LST"] == mission2.orbit_LST:
            score += 1
        # Return orbit score
        return score
    
    

    def instrumentsScore(self, instrument1, instrument2):
        score = 0.0
        # Score instrument type
        for type2 in instrument2.types:
            if instrument1["type"] == type2.name:
                score += 1
                break
        # Score instrument technology
        if instrument1["technology"] == instrument2.technology:
            score += 1
        # Score instrument geometry
        for geometry2 in instrument2.geometries:
            if instrument1["geometry"] == geometry2.name:
                score += 1
                break
        # Score instrument wavebands
        for waveband1 in instrument1["wavebands"]:
            for waveband2 in instrument2.wavebands:
                if waveband1 == waveband2.name:
                    score += 1/len(instrument1["wavebands"])
                    break
        # Return instruments score
        return score

    
    
    def instrumentsSimilarity(self, instruments1, instruments2):
        score = 0.0
        # Compute similarity matrix
        N = max(len(instruments1),len(instruments2))
        sim = np.zeros((N,N))
        for i1 in range(len(instruments1)):
            for i2 in range(len(instruments2)):
                sim[i1,i2] = self.instrumentsScore(instruments1[i1],instruments2[i2])
        # Find the best matches for i1xi2 (greedy)
        for k in range(len(instruments1)):
            i1i2 = np.argmax(sim)
            i1 = i1i2 / N
            i2 = i1i2 % N
            score += sim[i1,i2]/len(instruments1)
            sim[i1,:] = 0
            sim[:,i2] = 0
        return score

    def instrumentsMatchDataset(self, instruments2):
        matches = []
        instruments1 = self.instrumentsDataset
        N = len(instruments1)
        M = len(instruments2)
        # Compute similarity matrix
        sim = np.zeros((N,M))
        for i1 in range(N):
            for i2 in range(M):
                sim[i1,i2] = (self.instrumentsScore(instruments1[i1],instruments2[i2])*10)/4
        # Find the best matches for i2
        for i2 in range(M):
            i1i2 = np.argmax(sim[:,i2])
            i1 = i1i2 % N
            matches.append([instruments1[i1]["alias"],instruments2[i2].name,sim[i1,i2]])
        return matches

    def missionsSimilarity(self, orbit1, instruments1, missionsDatabase):
        maxScore = -1
        maxMission = None
        # Iterate over all the missions in the database
        for mission2 in missionsDatabase:
            score = 0
            # Get orbits similarity
            score += self.orbitsSimilarity(orbit1, mission2)
            # If score bigger than a threshold
            if(score > 1):
                # Get instruments similarities
                score += self.instrumentsSimilarity(instruments1, mission2.instruments)
            if score > maxScore:
                maxScore = score
                maxMission = mission2
        # Return result
        return [(maxScore*10)/7, maxMission]

    
    
    
    

    
    
    
    

    def archDifferences(self, arch1, arch2):
        result = []
        aa = []
        bb = []
        N = max(len(arch1),len(arch2))
        a = arch1 + ['']*(N - len(arch1))
        b = arch2 + ['']*(N - len(arch2))
        for o in range(N):
            i = 0
            while True:
                if i == len(a[o]):
                    break
                if b[o].find(a[o][i]) != -1:
                    b[o] = b[o].replace(a[o][i],'',1)
                    a[o] = a[o].replace(a[o][i],'',1)
                else:
                    i += 1
            aa.append(a[o])
            bb.append(b[o])
        for o1 in range(N):
            for i1 in range(len(aa[o1])):
                match = False
                for o2 in range(N):
                    if bb[o2].find(aa[o1][i1]) != -1:
                        bb[o2] = bb[o2].replace(aa[o1][i1],'',1)
                        match = True
                        break
                if match == True:
                    result.append(["moved", o1, o2, aa[o1][i1]])
                else:
                    result.append(["deleted", o1, aa[o1][i1]])
        for o2 in range(N):
            for i2 in range(len(bb[o2])):
                result.append(["added", o2, bb[o2][i2]])
        return result

    def matchSimilar(self, arch):
        res = []
        with open("EOSS_data.csv", "r") as csvfile:
            architectures = csv.reader(csvfile, delimiter=':')
            for row in architectures:
                diff = self.archDifferences(arch,json.loads(row[0]))
                # Get similar architectures (1 change maximum)
                if len(diff) == 1:
                    res.append([diff, float(row[1]), float(row[2])])
        return res

    def p(self, l):
        if not l: return [[]]
        return self.p(l[1:]) + [[l[0]] + x for x in self.p(l[1:])]

    
    
    
    
    
    
    

    def generateCritic1(self):
        out_filename = "CRITIC1.csv"
        f = open(out_filename, 'w')
        # For each instrument in each possible orbit (5*12=60)
        for orbit in self.orbitsDataset:
            for instrument in self.instrumentsDataset:
                # Get similar instruments from the database
                result = self.getSimilarInstruments(orbit, instrument)
                # Write results to the output file
                f.write(orbit["alias"]+"\t"+instrument["alias"]+"\t"+str(len(result))+"\t"+str([r.name for r in result])+"\n")
        f.close()


    def generateCritic2(self):
        out_filename = "CRITIC2.csv"
        f = open(out_filename, 'w')
        # Get missions in the database
        missionsDatabase = self.session.query(models.Mission)
        # For each combination of instruments in each possible orbit ((2^12)*5 = 20480)
        for orbit1 in self.orbitsDataset:
            for instruments1 in self.p(self.instrumentsDataset):
                # Get similar missions from the database
                result = self.missionsSimilarity(orbit1, instruments1, missionsDatabase)
                # Write results to the output file
                if result["maxScore"] != -1:
                    f.write(orbit1["alias"]+"\t"+str(sorted([i["alias"] for i in instruments1]))+"\t"+result[1].name+"\t"+str(result[0])+"\n")
        f.close()

        
        
        