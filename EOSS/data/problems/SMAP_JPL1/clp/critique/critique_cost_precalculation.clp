(defrule CRITIQUE-COST-PRECALCULATION::update-satellite-volume
    (declare (salience 100))
    ?miss <- (MANIFEST::Mission (Name ?n) (satellite-volume# nil) (satellite-dimensions $?dimensions&:(notempty$ $?dimensions)))
    =>
    (bind ?volume (*$ ?dimensions))
    (modify ?miss (satellite-volume# ?volume)))


(defrule CRITIQUE-COST-PRECALCULATION::find-satellite-max-size-ratio
    (declare (salience 90))
    (MANIFEST::Mission (Name ?n1)(satellite-volume# ?v1&~nil))
    (MANIFEST::Mission (Name ?n2&~?n1) (satellite-volume# ?v2&~nil))
    ?mratio <- (CRITIQUE-COST-PARAM::satellite-max-size-ratio (value ?r) (big-name ?bn) (small-name ?sn))
    =>
    (if (> ?v1 ?v2)
    then(bind ?temp-ratio (/ ?v1 ?v2))
        (bind ?temp-big-name ?n1)
        (bind ?temp-small-name ?n2)
    else(bind ?temp-ratio (/ ?v2 ?v1))
        (bind ?temp-big-name ?n2))
        (bind ?temp-small-name ?n1)
    (if (> ?temp-ratio ?r)
    then(modify ?mratio (value ?temp-ratio) (big-name ?temp-big-name) (small-name ?temp-small-name))))

(defrule CRITIQUE-COST-PRECALCULATION::find-satellite-max-cost-ratio
    (declare (salience 100))
    (MANIFEST::Mission (Name ?n1)(satellite-cost# ?c1&~nil))
    (MANIFEST::Mission (Name ?n2&~?n1) (satellite-cost# ?c2&~nil))
    ?cratio <- (CRITIQUE-COST-PARAM::satellite-max-cost-ratio (value ?r))
    =>
    (if (> ?c1 ?c2)
    then(bind ?temp-ratio (/ ?c1 ?c2))
        (bind ?temp-big-name ?n1)
        (bind ?temp-small-name ?n2)
    else(bind ?temp-ratio (/ ?c2 ?c1))
        (bind ?temp-big-name ?n2))
        (bind ?temp-small-name ?n1)
    (if (> ?temp-ratio ?r)
    then(modify ?cratio (value ?temp-ratio) (big-name ?temp-big-name) (small-name ?temp-small-name))))



(defrule CRITIQUE-COST-PRECALCULATION::launch-packaging-factors
    (declare (salience 100))
    (MANIFEST::Mission (id ?sat) (launch-vehicle ?lv&~nil) (Name ?n)
        (num-of-planes# ?np&~nil) (num-of-sats-per-plane# ?ns&~nil) (satellite-wet-mass ?m&~nil) (satellite-dimensions $?dim) 
        (orbit-type ?orb&~nil) (orbit-semimajor-axis ?a&~nil) (orbit-eccentricity ?e&~nil) (orbit-inclination ?i&~nil))
    =>
    (bind ?perf (get-performance ?lv ?orb (to-km (r-to-h ?a)) ?i))
    (bind $?diameter-height (MatlabFunctions getLaunchVehicleDimensions ?lv))
    (bind ?Dlv (nth$ 1 $?diameter-height))
    (bind ?Hlv (nth$ 2 $?diameter-height))

    (bind ?h (max$ $?dim))
    (bind ?dia (/ (get-diagonal (create$ (mid$ $?dim) (min$ $?dim)) 2)))

    (assert (CRITIQUE-COST-PARAM::launch-packaging-factors (name ?n) (performance-mass-ratio (/ ?m ?perf)) (diameter-ratio (/ ?dia ?Dlv)) (height-ratio (/ ?h ?Hlv))))
    (assert (CRITIQUE-COST-PARAM::launch-packaging-factors-temp (name ?n) (performance ?perf) (mass ?m) (diameter-lv ?Dlv) (diameter ?dia) (height-lv ?Hlv) (height ?h) (dimensions $?dim)))
)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(deffunction mid$ ($?list)
    (bind ?maximum (max$ $?list))
    (bind ?minimum (min$ $?list))
    (if (= ?maximum ?minimum) 
    then (return ?maximum)
    else (bind ?max-loc (member$ ?maximum $?list))
    (bind ?min-loc (member$ minimum $?list))
    (bind ?mid-loc (- 6 (+ ?max-loc ?min-loc)))
    (bind ?mid-value (nth$ ?mid-loc $?list))
    (return ?mid-value))
)

(deffunction get-diagonal ($?dim)
    (bind ?i1 (nth$ 1 $?dim))
    (bind ?i2 (nth$ 2 $?dim))
    (return (** (+ (** ?i1 2) (** ?i2 2)) 0.5))
)

(deffunction get-performance (?lv ?typ ?h ?i)
    (bind ?coeffs (MatlabFunctions getLaunchVehiclePerformanceCoeffs ?lv (str-cat ?typ "-" ?i)))
    (if (isempty$ ?coeffs) then 
        (throw new JessException (str-cat "get-performance: coeffs not found for lv typ h i = " ?lv " " ?typ " " ?h " " ?i)))
    (bind ?perf (dot-product$ ?coeffs (create$ 1 ?h (** ?h 2))))
    (return ?perf)
)