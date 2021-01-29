(defrule AGGREGATION::get-subobjective-scores
    "This rule gets subobjective scores from subobjective facts and puts 
    them into objective facts"
    
    ?sub <-(AGGREGATION::SUBOBJECTIVE (satisfaction ?sat&~nil) (index ?index) (parent ?papa) (satisfied-by ?whom))
    ?obj <- (AGGREGATION::OBJECTIVE (satisfaction nil) (id ?papa) (subobj-scores $?scors) (factHistory ?fh))
    (test (< (nth$ ?index $?scors) ?sat))
    =>
    (bind ?new-scors (replace$ $?scors ?index ?index ?sat))
    (modify ?obj (subobj-scores ?new-scors) (factHistory (str-cat "{R" (?*rulesMap* get AGGREGATION::get-subobjective-scores) " " ?fh " S" (call ?sub getFactId) "}")))
    )

	
(defrule AGGREGATION::compute-objective-scores
    "This rule computes objective scores when all subobjective scores are available
    by doing a weighted average"
    
	?obj <- (AGGREGATION::OBJECTIVE (satisfaction nil) (subobj-scores $?scors) (weights $?weights) (factHistory ?fh))
    (test (no-nils $?scors))
    =>
    (modify ?obj (satisfaction (dot-product$ $?weights $?scors)) (factHistory (str-cat "{R" (?*rulesMap* get AGGREGATION::compute-objective-scores) " " ?fh "}")))
    )

(defrule AGGREGATION::get-objective-scores
    "This rule gets objective scores from objective facts and puts 
    them into stakeholder facts"
    
    ?sub <- (AGGREGATION::OBJECTIVE (satisfaction ?sat&~nil) (index ?index) (parent ?papa) (satisfied-by ?whom))
    ?sh <- (AGGREGATION::STAKEHOLDER (satisfaction nil) (id ?papa) (obj-scores $?scors) (factHistory ?fh))
    (test (< (nth$ ?index $?scors) ?sat))
    =>
    (bind ?new-scors (replace$ $?scors ?index ?index ?sat))
    (modify ?sh (obj-scores ?new-scors) (factHistory (str-cat "{R" (?*rulesMap* get AGGREGATION::get-objective-scores) " " ?fh " S" (call ?sub getFactId) "}")))
    )

(defrule AGGREGATION::compute-stakeholder-scores
    "This rule computes stakeholder scores when all objective scores are available
    by doing a weighted average"
    ?sh <- (AGGREGATION::STAKEHOLDER (satisfaction nil) (obj-scores $?scors) (weights $?weights) (factHistory ?fh))
    (test (no-nils $?scors))
    =>
    ;(printout t "compute-stakeholder-scores " (?sh getFactId) crlf)
    (modify ?sh (satisfaction (dot-product$ $?weights $?scors)) (factHistory (str-cat "{R" (?*rulesMap* get AGGREGATION::compute-stakeholder-scores) " " ?fh "}")))
    )

(defrule AGGREGATION::get-stakeholder-scores
    "This rule gets stakeholder scores from stakeholder facts and puts 
    them into value facts"
    
    ?sub <- (AGGREGATION::STAKEHOLDER (satisfaction ?sat&~nil) (index ?index) (satisfied-by ?whom))
    ?val <- (AGGREGATION::VALUE (satisfaction nil) (sh-scores $?scors) (factHistory ?fh))
    (test (< (nth$ ?index $?scors) ?sat))
    =>
    (bind ?new-scors (replace$ $?scors ?index ?index ?sat))
    (modify ?val (sh-scores ?new-scors) (factHistory (str-cat "{R" (?*rulesMap* get AGGREGATION::get-stakeholder-scores) " " ?fh " S" (call ?sub getFactId) "}")))
    )


(defrule AGGREGATION::compute-value
    "This rule computes overall value by doing a weighted average of stakeholder scores"
    ?val <- (AGGREGATION::VALUE (satisfaction nil) (sh-scores $?scors) (weights $?weights) (factHistory ?fh))
    (test (no-nils $?scors))
    =>
    (modify ?val (satisfaction (dot-product$ $?weights $?scors)) (factHistory (str-cat "{R" (?*rulesMap* get AGGREGATION::compute-value) " " ?fh "}")))
    )

(defquery AGGREGATION::find-subobj-weight 
    (declare (variables ?subobj))
    (AGGREGATION::SUBOBJECTIVE (id ?subobj) (parent ?obj))
    (AGGREGATION::OBJECTIVE (id ?obj) (weights $?subobj-weights) (parent ?sh))
    (AGGREGATION::STAKEHOLDER (id ?sh) (weights $?obj-weights))
    (AGGREGATION::VALUE (weights $?sh-weights))
    )
