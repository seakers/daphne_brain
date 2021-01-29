;; ***************
;; Subsystem design
;;   4 rules
;; ***************

; power

;(batch ".\\clp\\eps_design_rules.clp")

; avionics or obdh
(defrule MASS-BUDGET::design-avionics-subsystem 
    "Computes comm subsystem mass using rules of thumb"
    (declare (salience 10))
    ?miss <- (MANIFEST::Mission (avionics-mass# nil) (payload-mass# ?m&~nil) (factHistory ?fh))
    =>
    (bind ?obdh-mass-coeff 0.0983)
    (bind ?obdh-mass (* ?m ?obdh-mass-coeff))
    (modify ?miss (avionics-mass# ?obdh-mass) (factHistory (str-cat "{R" (?*rulesMap* get MASS-BUDGET::design-avionics-subsystem) " " ?fh "}")))
    )

; adcs
;(batch ".\\clp\\adcs_design_rules.clp")

; thermal
(defrule MASS-BUDGET::design-thermal-subsystem 
    "Computes thermal subsystem mass using rules of thumb"
    (declare (salience 10))
    ?miss <- (MANIFEST::Mission (thermal-mass# nil) (payload-mass# ?m&~nil) (factHistory ?fh))
    =>
    (bind ?thermal-mass-coeff 0.0607)
    (bind ?thermal-mass (* ?m ?thermal-mass-coeff))
    (modify ?miss (thermal-mass# ?thermal-mass) (factHistory (str-cat "{R" (?*rulesMap* get MASS-BUDGET::design-thermal-subsystem) " " ?fh "}")))
    )

; propulsion

;(batch ".\\clp\\propulsion_design_rules.clp")

; structure

(defrule MASS-BUDGET::design-structure-subsystem 
    "Computes structure subsystem mass using rules of thumb"
    (declare (salience 10))
    ?miss <- (MANIFEST::Mission (structure-mass# nil) (payload-mass# ?m&~nil) (factHistory ?fh))
    =>
    
    (bind ?struct-mass (* 0.5462 ?m)); 0.75 
    
    (modify ?miss (structure-mass# ?struct-mass) (factHistory (str-cat "{R" (?*rulesMap* get MASS-BUDGET::design-structure-subsystem) " " ?fh "}")))
    )

; adapter

(defrule MASS-BUDGET::add-launch-adapter 
    "Computes launch adapter mass as 1% of satellite dry mass"
    (declare (salience 10))
    ?miss <- (MANIFEST::Mission (adapter-mass nil) (satellite-dry-mass ?m&~nil) (factHistory ?fh) )
    =>
    
    (bind ?adapter-mass (* 0.01 ?m)); 0.75 
    (modify ?miss (adapter-mass ?adapter-mass) (factHistory (str-cat "{R" (?*rulesMap* get MASS-BUDGET::add-launch-adapter ) " " ?fh "}")))
    )

; **************************************
; SUPPORTING QUERIES AND FUNCTIONS
; **************************************


    