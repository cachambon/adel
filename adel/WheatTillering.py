#
#       Adel.WheatTillering
#
#       Copyright 2006-2014 INRIA - CIRAD - INRA
#
#       File author(s): Christian Fournier <Christian.Fournier@supagro.inra.fr>
#
#       Distributed under the Cecill-C License.
#       See accompanying file LICENSE.txt or copy at
#           http://www.cecill.info/licences/Licence_CeCILL-C_V1-en.html
#
#       OpenAlea WebSite : http://openalea.gforge.inria.fr
#
###############################################################################

""" Wraping /extending  Wheat Tillering model used in Alinea.plantgen for calibration purposes
    Author : Christian Fournier
"""
import pandas
import numpy

from alinea.adel.plantgen import params, tools

#
# New propositions (C. Fournier, January 2014)
#
#index cohort delays with cohorts number (instead of primary_axis id of the same cohort) and add MS
cohort_delays = {(int(k.lstrip('T')) + 3):v for k,v in params.LEAF_NUMBER_DELAY_MS_COHORT.iteritems()}
cohort_delays[1] = 0
# Express time-delta between tiller regression and bolting in phyllochronic units
delta_reg = float(params.DELAIS_REG_MONT) / 110
#
# Add  defaults to handle 'less than MIN' datasets
#
# Defaults probabilities of appearance of tillers
primary_tiller_probabilities = {'T0':0,'T1':0.95, 'T2':0.85, 'T3':0.75, 'T4':0.4, 'T5':0.2, 'T6':0.1}
# relative probability  of emergence (ie actual to theoretical) of secondary tillers for the different cohorts (may be usfull for fitting?)
#secondary_tiller_probabilities = {i:1.0 for i in range(11)}
# number of elongated internodes (used in case hs_bolting is unknown, hs_bolting = hs_end - n_elongated_internode)
n_elongated_internode = 4
# mean number of ears per plant. This is better than ear density as it allows separate fitting of tillering and of and global scaling of axis per plant  with ear density
ears_per_plant = 2.5
# mean number of leaves on main stem
nff = 12.0


class WheatTillering(object):
    """Model of tiller population dynamics on wheat"""
    
    def __init__(self, primary_tiller_probabilities = primary_tiller_probabilities,
                       ears_per_plant = ears_per_plant,
                       nff = nff,
                       n_elongated_internode = n_elongated_internode,                   child_cohort_delay = params.FIRST_CHILD_DELAY,
                       #secondary_tiller_probabilities =secondary_tiller_probabilities,
                       cohort_delays = cohort_delays, #delays HS_0 MS -> HS_0 tillers HS=0 <=> emergence leaf 1
                       delta_reg = delta_reg):
        """ Instantiate model with default parameters """
        self.primary_tiller_probabilities = primary_tiller_probabilities
        self.ears_per_plant = ears_per_plant
        self.nff = nff
        self.n_elongated_internode = n_elongated_internode
        self.child_cohort_delay = child_cohort_delay
        #self.secondary_tiller_probabilities = secondary_tiller_probabilities
        self.cohort_delays = cohort_delays
        self.delta_reg = delta_reg

        
       
    def theoretical_probabilities(self):
        """ Computes cohort number, botanical position and theoretical probabilities of emergence all tillers using botanical position and probabilities of emergence of primary ones
        """
        #filter proba=0 axis
        axis_probabilities = {k:v for k,v in self.primary_tiller_probabilities.iteritems() if v > 0 }        
        cohort_probabilities = tools.calculate_decide_child_cohort_probabilities(axis_probabilities)
        _,res = tools.calculate_theoretical_cardinalities(1, 
                                                      cohort_probabilities,
                                                      axis_probabilities,
                                                      self.child_cohort_delay)
        return res
        
    def emited_cohort_density(self, plant_density = 1):
        proba = self.theoretical_probabilities()
        data = zip(*[(k[0],k[1],v) for k,v in proba.iteritems()])
        df = pandas.DataFrame({'axis': data[1],
                               'cohort' : data[0] ,
                               'probability':data[2], 
                               'primary':map(lambda x: not '.' in x, data[1])})
        grouped = df.groupby(['cohort'],group_keys=False)
        def _fun(x):
            cohort = x['cohort'].values[0]
            d = {'cohort': cohort, 
                 'delay': self.cohort_delays[cohort],
                 'primary_axis':x[x['primary']]['probability'].sum() * plant_density,
                 'other_axis' : x[~x['primary']]['probability'].sum() * plant_density   #'other_axis' : x[~x['primary']]['probability'].sum() * plant_density * self.secondary_tiller_probabilities[cohort],
                 }
            out = pandas.DataFrame(d,index = [x.index[0]])
            out['total_axis'] = out['primary_axis'] + out['other_axis']
            return out
        return grouped.apply(_fun)
        
    def axis_dynamics(self, plant_density = 1, hs_bolting = None):
        """ Compute axis density = f (HS_mean_MS)
            Parameters:
                - plant_density : plant per square meter
                - hs_bolting : Force Haun Stage of mean_MS at bolting (facultative).If None, hs_bolting is estimated using the number of elongated internodes
        """
        
        hs_max = self.nff
        if hs_bolting is None:
            hs_bolting = hs_max - self.n_elongated_internode
        hs_debreg = hs_bolting + self.delta_reg
        
        cohorts = self.emited_cohort_density(plant_density = plant_density)
        ear_density = self.ears_per_plant * plant_density
                
        # filter, if any, cohorts emited after regression start
        cohorts = cohorts[cohorts['delay'] <= hs_debreg]        
        # compute loss values that correspond to 100 percent loss for a cohort
        reverse_cohorts = cohorts.sort_index(by=['delay'], ascending = False)
        cohorts['cumulative_loss'] = reverse_cohorts['total_axis'].cumsum()       
        dmax = cohorts['total_axis'].sum()
        regression_rate = (ear_density - dmax) / (hs_max - hs_debreg)
        
        def _density(x, delays, cardinalities, total, cumulative_loss):
            if x < hs_debreg:
                d = cardinalities[delays <= x].sum()
            else :
                hs = min(x,hs_max)
                loss = - regression_rate * (hs - hs_debreg) #dmax - (dmax + reg)
                fraction_lost = (loss - cumulative_loss + total) / total
                fraction_lost = numpy.maximum(0,numpy.minimum(1,fraction_lost))
                d = (cardinalities * (1 - fraction_lost)).sum()           
            return d
               
        hs = numpy.arange(0,1.2 * hs_max,0.1)
        primary = map(lambda x: _density(x, cohorts['delay'], cohorts['primary_axis'], cohorts['total_axis'],cohorts['cumulative_loss']),hs)
        others = map(lambda x: _density(x, cohorts['delay'], cohorts['other_axis'], cohorts['total_axis'],cohorts['cumulative_loss']),hs)
        total = numpy.array(primary) + numpy.array(others)
        return pandas.DataFrame({'HS':hs, 'primary':primary, 'others' : others, 'total': total})
        