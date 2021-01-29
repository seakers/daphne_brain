;(require* modules "C:\\Users\\dani\\Documents\\My Dropbox\\Marc - Dani\\SCAN\\clp\\modules.clp")
;(require* templates "C:\\Users\\dani\\Documents\\My Dropbox\\Marc - Dani\\SCAN\\clp\\templates.clp")
;(require* more-templates "C:\\Users\\dani\\Documents\\My Dropbox\\Marc - Dani\\SCAN\\clp\\more_templates.clp")
;(require* functions "C:\\Users\\dani\\Documents\\My Dropbox\\Marc - Dani\\SCAN\\clp\\functions.clp")


; ******************************************
;                  ADCS DESIGN
;                    (4 rules)
; ******************************************
 
(defrule MASS-BUDGET::set-ADCS-type
    ?sat <- (MANIFEST::Mission (ADCS-requirement ?adcs&~nil) (ADCS-type nil)  (factHistory ?fh))
    =>
    (if (< ?adcs 0.1) then (bind ?typ three-axis)
        elif (< ?adcs 1) then (bind ?typ spinner)
        else (bind ?typ grav-grad))
    (modify ?sat (ADCS-type ?typ) (factHistory (str-cat "{R" (?*rulesMap* get MASS-BUDGET::set-ADCS-type) " " ?fh "}")))
    )

(defrule MASS-BUDGET::estimate-drag-coefficient
    ?sat <- (MANIFEST::Mission (drag-coefficient nil) (satellite-dimensions $?dim&:(> (length$ $?dim) 0)) (factHistory ?fh))
    =>
    (modify ?sat (drag-coefficient (estimate-drag-coeff $?dim)) (factHistory (str-cat "{R" (?*rulesMap* get MASS-BUDGET::estimate-drag-coefficient) " " ?fh "}")))
    )

(defrule MASS-BUDGET::estimate-residual-dipole
    " Anywhere between 0.1 and 20Am^2, 1Am2 for small satellite"
    ?sat <- (MANIFEST::Mission (residual-dipole nil) (factHistory ?fh))
    =>
    (modify ?sat (residual-dipole 5.0) (factHistory (str-cat "{R" (?*rulesMap* get MASS-BUDGET::estimate-residual-dipole) " " ?fh "}")))
    )

(defrule MASS-BUDGET::design-ADCS
    ?sat <- (MANIFEST::Mission (ADCS-requirement ?req&~nil) (satellite-dry-mass ?dry-mass&~nil) 
        (moments-of-inertia $?mom&:(> (length$ $?mom) 0)) (orbit-semimajor-axis ?a&~nil)
        (drag-coefficient ?Cd&~nil) (worst-sun-angle ?sun-angle&~nil)  
        (residual-dipole ?D&~nil) (slew-angle ?off-nadir&~nil)
        (satellite-dimensions $?dim&:(> (length$ $?dim) 0))
        (ADCS-mass# nil) (factHistory ?fh))
    =>
    (bind ?Iy (nth$ 2 $?mom)) (bind ?Iz (nth$ 3 $?mom))
    (bind ?x (nth$ 1 $?dim)) (bind ?y (nth$ 2 $?dim)) (bind ?z (nth$ 3 $?dim))
    (bind ?As (* ?x ?y))
    (bind ?cpscg (* 0.2 ?x)) (bind ?cpacg (* 0.2 ?x))
    (bind ?q 0.6)
    (bind ?torque (max-disturbance-torque 
            ?a ?off-nadir ?Iy ?Iz ?Cd ?As ?cpacg ?cpscg ?sun-angle ?D ?q))
    (bind ?ctrl-mass (estimate-att-ctrl-mass (compute-RW-momentum ?torque ?a)))
    (bind ?det-mass (estimate-att-det-mass ?req))
    (bind ?el-mass (+ (* 4 ?ctrl-mass) (* 3 ?det-mass)))
    (bind ?str-mass (* 0.01 ?dry-mass)); 
    (bind ?adcs-mass (+ ?el-mass ?str-mass))
    (modify ?sat (ADCS-mass# ?adcs-mass)(factHistory (str-cat "{R" (?*rulesMap* get MASS-BUDGET::design-ADCS) " " ?fh "}")))
    )


;; SUPPORTING QUERIES AND FUNCTIONS

(deffunction gravity-gradient-torque (?Iy ?Iz ?a ?off-nadir)
    "This function computes the gravity gradient disturbance torque.
    See SMAD page 367. Verified OK 9/18/12. "
    ; Tg = 3/2.*muE.*(1./R.^3).*(Iz-Iy).*sin(2.*theta.*Rad);
    
    (return (* 1.5 3.986e14 (/ 1 (** ?a 3)) (- ?Iz ?Iy) (sin ?off-nadir)))
    )

(deffunction aero-torque (?Cd ?As ?a ?cpacg)
    "This function computes the aerodynamic disturbance torque.
    See SMAD page 367. Verified OK 9/18/12."
    ; 
    (bind ?V (orbit-velocity ?a ?a))
    (bind ?rho (atmospheric-density (r-to-h ?a)))
    (return (* 0.5 ?rho ?As ?V ?V ?Cd ?cpacg))
    )

(deffunction solar-pressure-torque (?As ?q ?sun-angle ?cpscg)
    "This function computes the solar pressure disturbance torque.
    See SMAD page 367. Verified OK 9/18/12."
    (return (* (/ 1367 3e8) ?As (+ 1 ?q) (cos ?sun-angle) ?cpscg))
    )

(deffunction magnetic-field-torque (?D ?a)
    "This function computes the magnetic field disturbance torque.
    See SMAD page 367. Verified OK 9/18/12."
    (return (* 2 7.96e15 ?D (** ?a -3)))
    )

(deffunction estimate-drag-coeff (?list)
    "This function estimates the drag coefficient from the 
    dimensions of the satellite based on the article by Wallace et al
    Refinements in the Determination of Satellite Drag Coefficients: 
    Method for Resolving Density Discrepancies"
    
    (bind ?L-over-D (/ (max$ ?list) (min$ ?list)))
    (if (> ?L-over-D 3.0) then (return 3.3)
        else (return 2.2))
    )

(deffunction compute-disturbances (?a ?off-nadir ?Iy ?Iz ?Cd ?As ?cpacg ?cpscg ?sun-angle ?D ?q)
    (bind ?Tg (gravity-gradient-torque ?Iy ?Iz ?a ?off-nadir))
    (bind ?Ta (aero-torque ?Cd ?As ?a ?cpacg))
    (bind ?Tsp (solar-pressure-torque ?As ?q ?sun-angle ?cpscg))
    (bind ?Tm (magnetic-field-torque ?D ?a))
    (return (create$ ?Tg ?Ta ?Tsp ?Tm))
    )

(deffunction max-disturbance-torque (?a ?off-nadir ?Iy ?Iz ?Cd  ?As ?cpacg ?cpscg ?sun-angle ?D ?q)
    (return (max$ 
            (compute-disturbances ?a ?off-nadir ?Iy ?Iz ?Cd ?As ?cpacg ?cpscg ?sun-angle ?D ?q)))
    )

(deffunction compute-RW-momentum (?Td ?a)
    "This function computes the momentum storage capacity that a RW
    needs to have to compensate for a permanent sinusoidal disturbance torque
    that accumulates over a 1/4 period"
    
    (return (* (/ 1 (sqrt 2)) ?Td 0.25 (orbit-period ?a)))
    )

(deffunction estimate-att-ctrl-mass (?h)
    "This function estimates the mass of a RW from its momentum storage capacity.
    It can also be used to estimate the mass of an attitude control system"
    (return (* 1.5 (** ?h 0.6)))
    )

(deffunction estimate-RW-power (?T)
    "This function estimates the power of a RW from its torque authority"
    (return (* 200 ?T))
    )

(deffunction moment-of-inertia (?k ?m ?r)
    (return (* ?k ?m (** ?r 2)))
    )

(deffunction box-moment-of-inertia (?m ?dims)
    (return (map (lambda (?r) (return (moment-of-inertia (/ 1 6) ?m ?r))) ?dims))
    )

(deffunction estimate-att-det-mass (?acc)
    " This function estimates the mass of the sensor required for attitude determination
    from its knowledge accuracy requirement. It is based on data from BAll Aerospace, 
    Honeywell, and SMAD chapter 10 page 327"
    
    (return (* 10 (** ?acc -0.316)))
    )

(deffunction get-star-tracker-mass (?req)
    (if (< ?req 0.1) then (return 24.5)); Ball HAST 
    (if (< ?req 3) then (return 9.5)); Ball CT-602 
    (if (< ?req 5) then (return 6.5)); Ball CT-633
    (if (< ?req 52) then (return 3.2)); Ball HAST 
    )