;(defmodule DOWN-SELECTION)
;(deftemplate DOWN-SELECTION::MAX-COST (slot max-cost))
;(deftemplate DOWN-SELECTION::MIN-SCIENCE (slot min-benefit))
;(deftemplate DOWN-SELECTION::MIN-PARETO-RANK (slot min-pareto-rank))
;(deftemplate DOWN-SELECTION::MIN-UTILITY (multislot metrics) (multislot weights) (slot min-utility))

(defrule DOWN-SELECTION::delete-archs-too-expensive
    "Delete all archs with a lifecycle-cost that exceeds the max lifecycle-cost cap"
    (declare (salience 10))
    ?arch <- (MANIFEST::ARCHITECTURE  (benefit ?s) (lifecycle-cost ?c) (utility ?u) (pareto-ranking ?p) 
        (bitString ?seq) )
    (DOWN-SELECTION::MAX-COST (max-cost ?max-cost&:(< ?max-cost ?c)))
    =>
    (assert (REASONING::architecture-eliminated  (arch-str ?seq) (benefit ?s) (lifecycle-cost ?c) (utility ?u) (pareto-ranking ?p)  
            (reason-str delete-archs-too-expensive)))
    (retract ?arch)
    )

(defrule DOWN-SELECTION::delete-archs-too-little-utility
    "Delete all archs with a utility that does not meet min utility requirements"
    ?arch <- (MANIFEST::ARCHITECTURE  (benefit ?s) (lifecycle-cost ?c) (utility ?u) (pareto-ranking ?p)  
         (bitString ?seq) )
    (DOWN-SELECTION::MIN-UTILITY (min-utility ?min-utility&:(> ?min-utility ?u)))
    =>
    (assert (REASONING::architecture-eliminated  (arch-str ?seq) (benefit ?s) (lifecycle-cost ?c) (utility ?u) (pareto-ranking ?p)  
            (reason-str delete-archs-too-little-utility)))
    (retract ?arch)
    )

(defrule DOWN-SELECTION::delete-archs-not-enough-pareto-ranking
    "Delete all archs with a pareto ranking that does not meet min pareto ranking requirements"
    ?arch <- (MANIFEST::ARCHITECTURE (benefit ?s) (lifecycle-cost ?c) (utility ?u) (pareto-ranking ?p)  
        (bitString ?seq) )
    (DOWN-SELECTION::MIN-PARETO-RANK (min-pareto-rank ?min-pareto-rank&:(< ?min-pareto-rank ?p)))   
    =>
    (assert (REASONING::architecture-eliminated  (arch-str ?seq) (benefit ?s) (lifecycle-cost ?c) (utility ?u) (pareto-ranking ?p)  
            (reason-str delete-archs-not-enough-pareto-ranking)))
    (retract ?arch)
    )


(defrule DOWN-SELECTION::delete-archs-too-little-benefit
    "Delete all archs with a benefit that does not meet min benefit requirements"
    (declare (salience 10))
    ?arch <- (MANIFEST::ARCHITECTURE (benefit ?s) (lifecycle-cost ?c) (utility ?u) (pareto-ranking ?p)  
        (bitString ?seq) )
    (DOWN-SELECTION::MIN-SCIENCE (min-benefit ?min-benefit&:(> ?min-benefit ?s)))
    =>
    (retract ?arch)
     (assert (REASONING::architecture-eliminated (arch-str ?seq) (benefit ?s) (lifecycle-cost ?c) (utility ?u) (pareto-ranking ?p)  
            (reason-str delete-archs-too-little-benefit)))
    )
