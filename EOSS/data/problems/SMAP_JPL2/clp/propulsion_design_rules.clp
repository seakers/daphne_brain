; ***************************************
; PROPULSION SUBSYSTEM (AKM only, no ADCS)
;     (4 rules)
; ***************************************

(defrule MANIFEST::get-Isp-injection
    "This rule estimates the Isp injection from the type of propellant"
    ?miss <- (MANIFEST::Mission (propellant-injection ?prop&~nil) (Isp-injection nil) (factHistory ?fh))
    =>
    
    (modify ?miss (Isp-injection (get-prop-Isp ?prop)) (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::get-Isp-injection) " " ?fh "}")))
    )

(defrule MANIFEST::get-Isp-ADCS
    "This rule estimates the Isp ADCS from the type of propellant"
    ?miss <- (MANIFEST::Mission (propellant-ADCS ?prop&~nil) (Isp-ADCS nil) (factHistory ?fh))
    =>
    
    (modify ?miss (Isp-ADCS (get-prop-Isp ?prop)) (factHistory (str-cat "{R" (?*rulesMap* get MANIFEST::get-Isp-ADCS) " " ?fh "}")))
    )

(defrule MASS-BUDGET::compute-propellant-mass
    "This rule computes the propellant mass necessary for the DeltaV 
    using the rocket equation and assuming a certain Isp."
    
    ?miss <- (MANIFEST::Mission (satellite-dry-mass ?dry-mass&~nil) 
         (delta-V-injection ?dV-i&~nil) (delta-V ?dV&~nil)
        (Isp-injection ?Isp-i&~nil) (Isp-ADCS ?Isp-a&~nil) 
        (propellant-mass-injection nil) (propellant-mass-ADCS nil) (factHistory ?fh))
    =>
    (bind ?mp-inj (rocket-equation-mf-dV-to-mp ?dV-i ?Isp-i ?dry-mass))
    (bind ?mp-a (rocket-equation-mf-dV-to-mp (- ?dV ?dV-i) ?Isp-a ?dry-mass))
    (modify ?miss (propellant-mass-injection ?mp-inj) (propellant-mass-ADCS ?mp-a) (factHistory (str-cat "{R" (?*rulesMap* get MASS-BUDGET::compute-propellant-mass) " " ?fh "}"))); wet mass
    )

(defrule MASS-BUDGET::design-propulsion-AKM 
    "Computes dry AKM mass using rules of thumb: 
    94% of wet AKM mass is propellant, 6% motor"
    
    ?miss <- (MANIFEST::Mission (propulsion-mass# nil) 
        (propellant-mass-injection ?m&~nil) (factHistory ?fh))

        =>
   	
    (modify ?miss (propulsion-mass# (* ?m (/ 6 94))) (factHistory (str-cat "{R" (?*rulesMap* get MASS-BUDGET::design-propulsion-AKM) " " ?fh "}")))
    )

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; SUPPORTING QUERIES AND FUNCTIONS
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;


(deffunction rocket-equation-mi-dV-to-mp (?dV ?Isp ?mi)
    ; mprop = mwet*(1-exp(-dV/V0))
    (return (* ?mi (- 1 (exp (/ ?dV (* -9.81 ?Isp))))))
    )

(deffunction rocket-equation-mf-dV-to-mp (?dV ?Isp ?mf)
    ; mprop = mdry*(-1+exp(dV/V0))
    (return (* ?mf (- (exp (/ ?dV (* 9.81 ?Isp))) 1)))
    )

(deffunction get-prop-Isp (?prop)
    (bind ?props (create$ solid hydrazine LH2))
    (bind ?Isps (create$ 210 290 450))
    
    (bind ?ind (member$ ?prop ?props))
    (if (eq ?ind FALSE) then (printout t "get-prop-Isp: propellant not found" crlf) (return FALSE)
    else (return (nth$ ?ind ?Isps)))
    )
