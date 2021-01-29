(defrule FUZZY-AGGREGATION::get-subobjective-scores
    "This rule gets subobjective scores from subobjective facts and puts 
    them into objective facts"
    
    ?sub <- (AGGREGATION::SUBOBJECTIVE  (satisfaction ?sat&~nil) (index ?index) (parent ?papa) (satisfied-by ?whom) (fuzzy-value ?fv))
    ?obj <- (AGGREGATION::OBJECTIVE (satisfaction nil) (id ?papa) (subobj-scores $?scors) (subobj-fuzzy-scores $?fuzzy-scors) (factHistory ?fh))
    (test (< (nth$ ?index $?scors) ?sat))
    =>
    (bind ?new-scors (replace$ $?scors ?index ?index ?sat))
    (bind ?new-fuzzy-scors (replace$ $?fuzzy-scors ?index ?index ?fv))
    (modify ?obj (subobj-scores ?new-scors) (subobj-fuzzy-scores ?new-fuzzy-scors) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-AGGREGATION::get-subobjective-scores) " " ?fh " S" (call ?sub getFactId) "}")))
    )

(defrule FUZZY-AGGREGATION::compute-objective-scores
    "This rule computes objective scores when all subobjective scores are available
    by doing a weighted average"
    ?obj <- (AGGREGATION::OBJECTIVE (satisfaction nil) (subobj-scores $?scors) 
        (weights $?weights) (subobj-fuzzy-scores $?fuzzy-scors) (factHistory ?fh))
    (test (no-nils $?scors))
    =>
    (modify ?obj (satisfaction (dot-product$ $?weights $?scors)) (fuzzy-value (fuzzy-dot-product$ $?weights $?fuzzy-scors)) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-AGGREGATION::compute-objective-scores) " " ?fh "}")))
    )

(defrule FUZZY-AGGREGATION::get-objective-scores
    "This rule gets objective scores from objective facts and puts 
    them into stakeholder facts"
    
    ?sub <-(AGGREGATION::OBJECTIVE (satisfaction ?sat&~nil) (index ?index) (parent ?papa) (satisfied-by ?whom) (fuzzy-value ?fv))
    ?sh <- (AGGREGATION::STAKEHOLDER (satisfaction nil) (id ?papa) (obj-scores $?scors) (obj-fuzzy-scores $?fuzzy-scors) (factHistory ?fh))
    (test (< (nth$ ?index $?scors) ?sat))
    =>
    (bind ?new-scors (replace$ $?scors ?index ?index ?sat))
    (bind ?new-fuzzy-scors (replace$ $?fuzzy-scors ?index ?index ?fv))
    (modify ?sh (obj-scores ?new-scors) (obj-fuzzy-scores ?new-fuzzy-scors) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-AGGREGATION::get-objective-scores) " " ?fh " S" (call ?sub getFactId) "}")))
    )

(defrule FUZZY-AGGREGATION::compute-stakeholder-scores
    "This rule computes stakeholder scores when all objective scores are available
    by doing a weighted average"
    ?sh <- (AGGREGATION::STAKEHOLDER (satisfaction nil) (obj-fuzzy-scores $?fuzzy-scors)  (obj-scores $?scors) (weights $?weights) (factHistory ?fh))
    (test (no-nils $?scors))
    =>
    ;(printout t "compute-stakeholder-scores " (?sh getFactId) crlf)
    (modify ?sh (satisfaction (dot-product$ $?weights $?scors)) (fuzzy-value (fuzzy-dot-product$ $?weights $?fuzzy-scors)) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-AGGREGATION::compute-stakeholder-scores) " " ?fh "}")))
    )

(defrule FUZZY-AGGREGATION::get-stakeholder-scores
    "This rule gets stakeholder scores from stakeholder facts and puts 
    them into value facts"
    
    ?sub <- (AGGREGATION::STAKEHOLDER (satisfaction ?sat&~nil) (index ?index) (satisfied-by ?whom) (fuzzy-value ?fv))
    ?val <- (AGGREGATION::VALUE (satisfaction nil) (sh-scores $?scors) (sh-fuzzy-scores $?fuzzy-scors) (factHistory ?fh))
    (test (< (nth$ ?index $?scors) ?sat))
    =>
    (bind ?new-scors (replace$ $?scors ?index ?index ?sat))
    (bind ?new-fuzzy-scors (replace$ $?fuzzy-scors ?index ?index ?fv))
    (modify ?val (sh-scores ?new-scors) (sh-fuzzy-scores ?new-fuzzy-scors) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-AGGREGATION::get-stakeholder-scores) " " ?fh " S" (call ?sub getFactId) "}")))
    )


(defrule FUZZY-AGGREGATION::compute-value
    "This rule computes overall value by doing a weighted average of stakeholder scores"
    ?val <- (AGGREGATION::VALUE (satisfaction nil) (sh-fuzzy-scores $?fuzzy-scors) (sh-scores $?scors) (weights $?weights) (factHistory ?fh))
    (test (no-nils $?scors))
    =>
    (modify ?val (satisfaction (dot-product$ $?weights $?scors)) (fuzzy-value (fuzzy-dot-product$ $?weights $?fuzzy-scors)) (factHistory (str-cat "{R" (?*rulesMap* get FUZZY-AGGREGATION::compute-value) " " ?fh "}")))
    )

(defquery FUZZY-AGGREGATION::find-subobj-weight 
    (declare (variables ?subobj))
    (AGGREGATION::SUBOBJECTIVE (id ?subobj) (parent ?obj))
    (AGGREGATION::OBJECTIVE (id ?obj) (weights $?subobj-weights) (parent ?sh))
    (AGGREGATION::STAKEHOLDER (id ?sh) (weights $?obj-weights))
    (AGGREGATION::VALUE (weights $?sh-weights))
    )
