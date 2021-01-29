;; EXPLANATION RULES
;(batch templates.clp)

(defrule REASONING::if-full-then-clear-partials 
    "Retract all partial satisfaction facts if there is a full satisfaction corresponding to that subobjective" 
    (declare (salience 10))
    (REASONING::fully-satisfied (subobjective  ?subobj ))
     ?f <- (REASONING::partially-satisfied (subobjective  ?subobj )) 
    => 
     (retract ?f)
    )


(defrule REASONING::subobj-fully-satisfied "Explain why the subobjective is fully satisfied"  
    (REASONING::fully-satisfied (subobjective  ?subobj ) (parameter ?p) (objective ?o) (taken-by ?who)) 
    => 
    ;(bind ?str (str-cat "Subobjective " ?subobj " requiring parameter " ?p " for studying " ?o " is fully satisfied by " ?who )) 
    ;(printout t ?str crlf)
    (matlabf explanation_facility ?subobj ?p ?o ?who full)
    )

(defrule REASONING::subobj-partially-satisfied "Explain why the subobjective is partially satisfied"
    (REASONING::partially-satisfied (subobjective  ?subobj ) (parameter ?p) (objective ?o)  (taken-by ?who) (attribute ?att)) 
    => 
    ;(bind ?str (str-cat "Subobjective " ?subobj " requiring parameter " ?p " for studying " ?o " is partially satisfied by " ?who " because " ?att))
    ;(printout t ?str crlf)
    (matlabf explanation_facility ?subobj ?p ?o ?who ?att)
    )

(defquery REASONING::who-satisfies-subobj "Finds who satisfies a given subobjective"
    (declare (variables ?subobj))
    (or 
        (REASONING::fully-satisfied (subobjective ?subobj )  (taken-by ?who))
    	(REASONING::partially-satisfied (subobjective ?subobj )  (taken-by ?who) (attribute ?att))
        )
    )

(defquery REASONING::search-eliminated-architecture-by-sequence
    (declare (variables ?seq))
    (REASONING::architecture-eliminated (arch-id ?seq) (arch-str ?str) 
        (benefit ?s) (lifecycle-cost ?c) (utility ?u) (pareto-ranking ?p)   
            (reason-str ?reason))
    )

(defquery REASONING::search-eliminated-architecture-by-str
    (declare (variables ?str))
    (REASONING::architecture-eliminated (arch-id ?seq) (arch-str $?str) 
        (benefit ?s) (lifecycle-cost ?c) (utility ?u) (pareto-ranking ?p)   
            (reason-str ?reason))
    )


(deffunction why-was-arch-eliminated (?str)
    (bind ?result (run-query* REASONING::search-eliminated-architecture-by-str ?str))
    (while (?result next) 
        ;(printout t "architecture " (?result getString seq) " eliminated because of " (?result getString reason) crlf)
        (return (?result getString reason))
        )
    )

(deffunction get-arch-eliminated-science (?seq)
    (bind ?result (run-query* REASONING::search-eliminated-architecture-by-sequence ?seq))
    (while (?result next) 
        ;(printout t "architecture " (?result getString seq) " eliminated because of " (?result getString reason) crlf)
        (return (?result getDouble s))
        )
    )

(deffunction get-arch-eliminated-cost (?seq)
    (bind ?result (run-query* REASONING::search-eliminated-architecture-by-sequence ?seq))
    (while (?result next) 
        ;(printout t "architecture " (?result getString seq) " eliminated because of " (?result getString reason) crlf)
        (return (?result getDouble c))
        )
    )