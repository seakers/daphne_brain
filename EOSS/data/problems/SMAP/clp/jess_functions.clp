;; **************************************************
;; FUNCTIONS TO HANDLE LISTS
;; **************************************************
(deffunction count$ (?list ?el)
    (if (eq (length$ ?list) 1) then
    	(if (eq (nth$ 1 ?list) ?el) then
        	(return 1)
        else
        	(return 0)
        )
    else
    	(if (eq (nth$ 1 ?list) ?el) then
        	(bind ?x 1)    
        else
            (bind ?x 0)
        )
        (return (+ ?x (count$ (rest$ ?list) ?el)))    
    )
)

(deffunction append$ (?list ?el)
(return (insert$ ?list (+ 1 (length$ ?list)) ?el)))

(deffunction append-all$ (?list ?these)
    (foreach ?el ?these 
        (bind ?list (append$ ?list ?el)))
    (return ?list)
    )

(deffunction remove$ (?list ?el)
(bind ?ind (member$ ?el ?list))
(if (numberp ?ind) then (return (delete$ ?list ?ind ?ind)) 
else (return FALSE)))

(deffunction map$ (?func ?list)
    (bind ?res (create$ ))
    (foreach ?elem ?list
        (bind ?res (insert$ ?res (+ 1 (length$ ?res)) (apply ?func ?elem))))
    )
(deffunction zeros$ (?N)
    (bind ?list (create$ ))
    (for (bind ?i 1) (<= ?i ?N) (++ ?i)
        (bind ?list (append$ ?list 0)))
    (return ?list)
    )

(deffunction ones$ (?N)
    (bind ?list (create$ ))
    (for (bind ?i 1) (<= ?i ?N) (++ ?i)
        (bind ?list (append$ ?list 1)))
    (return ?list)
    )

(deffunction repeat$ (?el ?N)
    (bind ?list (create$ ))
    (for (bind ?i 1) (<= ?i ?N) (++ ?i)
        (bind ?list (append$ ?list ?el)))
    (return ?list)
    )


(deffunction nils$ (?N)
    (bind ?list (create$ ))
    (for (bind ?i 1) (<= ?i ?N) (++ ?i)
        (bind ?list (append$ ?list nil)))
    (return ?list)
    )

;(deffunction map2$ (?func ?list)
;    (return (eval (str-cat "(" ?func " " (implode$ ?list) ")")))
;    )

(deffunction last$ (?list)
    (return (nth$ (length$ ?list) ?list))
    )

(deffunction del-element$ (?list ?elem)
    (bind ?index (member$ ?elem ?list))
    (return (delete$ ?list ?index ?index))
    )
(deffunction del-all$ (?list ?indexes)
    (bind ?list2 (create$ ))
    (for (bind ?i 1) (<= ?i (length$ ?list)) (++ ?i) 
    (if (numberp (member$ ?i ?indexes)) then (continue) else (bind ?list2 (add-element$ ?list2 (nth$ ?i ?list)))))
    (return ?list2)
    )

(deffunction add-element$ (?list ?elem)
    (return (insert$ ?list (+ 1 (length$ ?list)) ?elem))
    )

(deffunction find$ (?elem ?list)
    (bind ?indexes (create$ )) (bind ?n 1)
    (for (bind ?i 1) (<= ?i (length$ ?list)) (++ ?i) 
        (if (eq ?elem (nth$ ?i ?list)) then 
            (bind ?indexes (insert$ ?indexes ?n ?i)) (bind ?n (+ ?n 1)))
        )
    (return ?indexes)
    )


(deffunction replace-all$ (?list ?old ?new)
    (for (bind ?i 1) (<= ?i (length$ ?list)) (++ ?i)
        (if (eq (nth$ ?i ?list) ?old) then (bind ?list (replace$ ?list ?i ?i ?new))))
    (return ?list)
    )

(deffunction set-all$ (?list ?indexes ?new)
    (for (bind ?i 1) (<= ?i (length$ ?list)) (++ ?i)
        (if (numberp (member$ ?i ?indexes)) then (bind ?list (replace$ ?list ?i ?i ?new))))
    (return ?list)
    )

(deffunction .*$ (?x ?y)
    ;(printout t " call .*$ x = " ?x " y = " ?y crlf) 
    (if (not (and (listp ?x) (listp ?y))) then 
        (if (and (numberp ?x) (numberp ?y)) then (return (* ?x ?y)) else (return 0))) 
    (bind ?z (create$ )) 
    (for (bind ?i 1) (<= ?i (length$ ?x)) (++ ?i) 
        (bind ?tmp (* (nth$ ?i ?x) (nth$ ?i ?y))) (bind ?z (insert$ ?z ?i ?tmp))) 
    (return ?z))

(deffunction .+$ (?x ?y)
    ;(printout t " call .+$ x = " ?x " y = " ?y crlf)
    ;(printout t " x is list = " (listp ?x) " y is list = " (listp ?y) crlf)  
    (if (not (and (listp ?x) (listp ?y))) then 
        (if (numberp ?x) then (return (+ ?x ?y)) else (return 0)))
    ;(printout t "went past " crlf) 
    (bind ?z (create$ )) 
    (for (bind ?i 1) (<= ?i (length$ ?x)) (++ ?i) 
        (bind ?tmp (+ (nth$ ?i ?x) (nth$ ?i ?y))) (bind ?z (insert$ ?z ?i ?tmp)))
    ;(printout t " result = " ?z crlf) 
    (return ?z))

(deffunction sum$ (?list)
    (if (not (listp ?list)) then (if (numberp ?list) then (return ?list) else (return 0))) 
    (if (eq (length$ ?list) 1) then (return (nth$ 1 ?list))
        else (return (+ (nth$ 1 ?list) (sum$ (rest$ ?list))))) 
    )

(deffunction *$ (?list)
    (if (not (listp ?list)) then (if (numberp ?list) then (return ?list) else (return 0))) 
    (if (eq (length$ ?list) 1) then (return (nth$ 1 ?list))
        else (return (* (nth$ 1 ?list) (*$ (rest$ ?list))))) 
    )

; this other implementation is simpler and also works, but perhaps less efficient
;(deffunction max$ (?list)
;    (return (eval (str-cat "max " (implode$ ?list))))
;    )

(deffunction max$ (?list)
    ;(printout t "max$ " ?list " is list " crlf)
    (if (not (listp ?list)) then (if (numberp ?list) then (return ?list) else (return 0))) 
    (if (eq (length$ ?list) 0) then (return 0))
    (bind ?car (nth$ 1 ?list))
    (if (eq (length$ ?list) 1) then (return ?car)
        else (return (max ?car (max$ (rest$ ?list)))))  
    )

(deffunction min$ (?list)
    (if (not (listp ?list)) then (if (numberp ?list) then (return ?list) else (return 0))) 
    (bind ?car (nth$ 1 ?list))
    (if (eq (length$ ?list) 1) then (return ?car)
        else (return (min ?car (min$ (rest$ ?list)))))  
    )
(deffunction dot-product$ (?x ?y) 
    (return (sum$ (.*$ ?x ?y))))

(deffunction isempty$ (?list)
    (return (eq (length$ ?list) 0)))

(deffunction notempty$ (?list)
    (return (eq (isempty$ ?list) FALSE)))

(deffunction create-list-n$ (?n)
    (bind ?list (create$ ))
    (for (bind ?i 1) (<= ?i ?n) (++ ?i)
        (bind ?list (insert$ ?list ?i 0)))
    (return ?list))

(deffunction find-bin (?op ?val ?thr)
    "This function finds the interval within a set of intervals specified by their thresholds
    ?thr (ordered from best to worst) to which a number ?val belongs"
    
    (bind ?n 1)
    (while (<= ?n (length$ ?thr)  )
        ;(printout t "n = "?n " op = "?op " val = " ?val " thr = " (nth$ ?n ?thr) crlf)
        (if (apply ?op ?val (nth$ ?n ?thr)) then (return ?n))
        (++ ?n)
        )
    ;(if (> ?n (length$ ?thr)) then (printout 
     ;       t "find-bind did not find any matching bin for val = " ?val " thr = " ?thr crlf))
	(return ?n)
    )

(deffunction find-bin-txt (?val ?thr)
    "This function finds the interval within a set of intervals specified by their thresholds
    ?thr (ordered from best to worst) to which a number ?val belongs. It works for text values
    and thresholds"

	(return (find-bin "eq" ?val ?thr))
    )

(deffunction find-bin-num (?val ?thr)
    "This function finds the interval within a set of intervals specified by their thresholds
    ?thr (ordered from best to worst) to which a number ?val belongs"
    
    (if (>= (nth$ 1 ?thr) (nth$ (length$ ?thr) ?thr)) then 
        (bind ?op ">=") else (bind ?op "<="))
    (return (find-bin ?op ?val ?thr))
    )

(deffunction no-nils (?list)
    (foreach ?el ?list
        (if (< ?el 0) then (return FALSE)))
    ;(printout t " no-nils authorized for " ?list crlf)
    (return TRUE)
    )

(deffunction get-elems$ (?indexes ?list)
    (bind ?res (create$))
    (for (bind ?i 1) (<= ?i (length$ ?indexes)) (++ ?i)
        (bind ?index (nth$ ?i ?indexes))
        (bind ?el (nth$ ?index ?list))
        (bind ?res (append$ ?res ?el)))
    (return ?res)
    )

(deffunction get-elems-bin$ (?indexes ?list)
    "This function returns the elements in list specified by the 0-1 indexes list"
    (bind ?res (create$))
    (for (bind ?i 1) (<= ?i (length$ ?indexes)) (++ ?i)
        (if (or (eq (nth$ ?i ?indexes) 1) (eq (nth$ ?i ?indexes) 1.0)) then  
            (bind ?res (append$ ?res (nth$ ?i ?list)))))
    (return ?res)
    )

(deffunction contains$ (?el ?list)
    (return (numberp (member$ ?el ?list)))
    )


(deffunction not-contains$ (?el ?list)
    (return (not (numberp (member$ ?el ?list))))
    )

(deffunction contains-all$ (?these ?list)
    (foreach ?el ?these
        (if (not-contains$ ?el ?list) then (return FALSE)))
    (return TRUE)
    )

(deffunction not-contains-all$ (?these ?list)
    (return (not (contains-all$ ?these ?list)))
    )
;; **************************************************
;; MISCELLANEOUS ENGINEERING FUNCTIONS
;; **************************************************
(deffunction infinityp (?x)
(return (and (numberp ?x) (> ?x 1e20))))

(deffunction +nils (?x $?rest)
    (if (eq ?x nil) then (bind ?x 0))
    (if (eq (length$ $?rest) 0) then (return ?x) 
        else (return (+ ?x (+nils (nth$ 1 $?rest) (rest$ $?rest)))))
    )

(deffunction dB-to-lin (?dB)
    (return (** 10 (/ ?dB 10)))
    )

(deffunction lin-to-dB (?lin)
    (return (* 10 (log10 ?lin)))
    )

(deffunction to-rad (?x)
    (return (* ?x (pi) (/ 1 180))))

(deffunction to-deg (?x)
    (return (* ?x 180 (/ 1 (pi)))))

(deffunction sin (?x)
    (return (call java.lang.Math sin (to-rad ?x)))
    )

(deffunction cos (?x)
    (return (call java.lang.Math cos (to-rad ?x)))
    )

(deffunction tan (?x)
    (return (call java.lang.Math tan (to-rad ?x)))
    )

(deffunction asin (?x)
    (return (to-deg (call java.lang.Math asin ?x)))
    )

(deffunction acos (?x)
    (return (to-deg (call java.lang.Math acos ?x)))
    )

(deffunction atan (?x)
    (return (to-deg (call java.lang.Math atan ?x)))
    )

(deffunction dec2bin (?dec ?N)
    ;(bind ?x (Matlab jde2bi ?dec ?N))
    ;(if (listp ?x) then (return ?x) else (return (create$ ?x)))
	(bind ?bin (create$ ))
	(for (bind ?i 1) (<= ?i ?N) (++ ?i)
		(bind ?q (floor (/ ?dec 2)))
		(bind ?r (- ?dec (* ?q 2)))
		(bind ?bin (append$ ?bin ?r))
		(bind ?dec ?q)
	)
	(return ?bin)
    )

(deffunction floor (?n)
	(bind ?r (round ?n))
	(if (>= (- ?n ?r) 0) then
		(return ?r)
	else
		(return (- ?r 1))
		)
)	

(deffunction ceil (?n)
	(bind ?r (round ?n))
	(if (> (- ?n ?r) 0) then
		(return (+ 1 ?r))
	else
		(return ?r)
		)
)	

(deffunction transpose-decimal$ (?arr ?n)
    (bind ?x (matlabf transpose_decimal ?arr ?n))
    (if (listp ?x) then (return ?x) else (return (create$ ?x)))
    )
(deffunction get-indexes-constel$ (?arr ?nc ?i)
    (bind ?x (matlabf get_indexes_constel ?arr ?nc ?i))
    (if (listp ?x) then (return ?x) else (return (create$ ?x)))
    )
(deffunction consistent-gs-payload-alloc (?nc ?np ?gs-a)
    (return (matlabf consistent_gs_payload_alloc ?nc ?np ?gs-a))
    )

;; *******************
;; Functions to handle intervals
;; ******************

(deffunction fuzzyprod (?fv1 ?fv2)
    ;(printout t "fuzzyprod fv1 = " (call ?fv1 toString) " fv2 = " (call ?fv2 toString) crlf )
    (return (call ?fv1 prod ?fv2))
    )

(deffunction fuzzyscprod (?fv1 ?lambda)
    ;(printout t "fuzzyprod fv1 = " (call ?fv1 toString) " lambda = " ?lambda crlf )
    (return (call ?fv1 times ?lambda))
    )

(deffunction fuzzyscprod$ (?fvs ?lambdas)
    ;(printout t "fuzzyprod fv1 = " (call ?fv1 toString) " fv2 = " (call ?fv2 toString) crlf )
    (bind ?list (create$ ))
    (for (bind ?i 1) (<= ?i (length$ ?fvs)) (++ ?i)
        (bind ?fv (nth$ ?i ?fvs)) (bind ?w (nth$ ?i ?lambdas))
        ;(printout t (call ?fv toString) " " ?w)
        (bind ?list (insert$ ?list ?i (fuzzyscprod ?fv ?w))))
    (return ?list)
    )

(deffunction fuzzysum (?fv1 ?fv2)
    ;(printout t "fuzzyprod fv1 = " (call ?fv1 toString) " fv2 = " (call ?fv2 toString) crlf )
    (return (call ?fv1 add ?fv2))
    )

(deffunction fuzzy-dot-product$ (?scalars ?fvs) 
    (return (fuzzysum$ (fuzzyscprod$ ?fvs ?scalars))))

(deffunction fuzzysum$ (?list)
    (if (not (listp ?list)) then (if (numberp ?list) then (return ?list) else (return 0))) 
    (if (eq (length$ ?list) 0) then (return 0))
    (bind ?car (nth$ 1 ?list))
    (if (eq (length$ ?list) 1) then (return ?car)
        else (return (fuzzysum ?car (fuzzysum$ (rest$ ?list)))))  
    )


(deffunction fuzzyprod$ (?list)
    (if (not (listp ?list)) then (if (numberp ?list) then (return ?list) else (return 0))) 
    (if (eq (length$ ?list) 0) then (return 0))
    (bind ?car (nth$ 1 ?list))
    (if (eq (length$ ?list) 1) then (return ?car)
        else (return (fuzzyprod ?car (fuzzyprod$ (rest$ ?list)))))  
    )

(deffunction fuzzyvalprod$ (?list)
    (return (fuzzyprod$ (map$ fuzzyval ?list)))
    )

(deffunction fuzzyval (?fuzz)
    ;(printout t fuzzyval " " ?fuzz crlf)
    (return (new FuzzyValue "Value" ?fuzz "utils" (matlabf get_value_inv_hashmap)))
    )

(deffunction defuzzyfy (?fuzz)
    (return (call (fuzzyval ?fuzz) getNum_val))
    )    

(deffunction cost-fv (?avg ?delta)
    (return (new FuzzyValue "Cost" (new Interval "delta" ?avg ?delta) "FY04$M"))
    )

(deffunction value-fv (?lo ?hi)
    (return (new FuzzyValue "Value" (new Interval "interval" ?lo ?hi) "utils" (matlabf get_value_inv_hashmap)))
    )

(deffunction as-interval(?num)
(if (java-objectp ?num) then 
    (if (eq ((?num getClass) getCanonicalName) "Interval") then (return ?num)) 
else
(return (new Interval "interval" ?num ?num))))

(deffunction sum* (?list)
(bind ?list (map as-interval ?list))
(bind ?car (nth$ 1 ?list))
(if (eq (length$ ?list) 1) then (return ?car)
        else (return (?car add (sum* (rest$ ?list))))) 
)

(deffunction compute-fuzzy-payload-cost (?fz-m ?n)
	(bind ?nrec ((sum* (create$ (?fz-m times 339) (* 5127 ?n))) times 0.001))
    (bind ?rec ((?fz-m times 189) times 0.001))
    (bind ?cost (sum* (create$ ?nrec ?rec)))
    (return ?cost))

; ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Functions to generate random numbers
; ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(deffunction rand-bool (?p)  
    "random boolean biased according to ?p (smaller p = rare true)"
    (return (< (random) (* ?p 65536)))
    )

(deffunction rand-int (?N)
    "random integer from 1 to ?N"
    (bind ?x (+ 1 (round (* (- ?N 1) (/ (random) 65536)))))
    )

(deffunction rand-elem$ (?vec)
    (return (nth$ (rand-int (length$ ?vec)) ?vec))
    )

; ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Functions to handle selection problems
; ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(deffunction add-random-missing-element (?current ?all)
    "Adds random element from ?all& not ?current to ?current"
    (bind ?candidates (complement$ ?current ?all)) 
    (if (> (length$ ?candidates) 0) then (bind ?to-add (nth$ (rand-int (length$ ?candidates)) ?candidates)) (return (append$ ?current ?to-add )) 
        else (return ?current)))
(deffunction get-random-missing-element (?current ?all)
    "Returns random element from ?all& not ?current"
    (bind ?candidates (complement$ (create$ ?current) ?all)) 
    (if (> (length$ ?candidates) 0) then (bind ?to-add (nth$ (rand-int (length$ ?candidates)) ?candidates)) (return ?to-add) 
        else (return ?current)))
(deffunction remove-random-element (?current)
    "Removes random element from ?current"
    (if (> (length$ ?current) 0) then (bind ?to-rem (nth$ (rand-int (length$ ?current)) ?current)) (return (remove$ ?current ?to-rem)) 
        else (return ?current)))

(deffunction remove-random-element2 (?current)
    "Removes random element from ?current"
    (bind ?index (rand-int (length$ ?current)))
    (if (> (length$ ?current) 0) then (bind ?to-rem (nth$ ?index ?current)) (return (create$ ?index (remove$ ?current ?to-rem))) 
        else (return (create$ 0 ?current))))

; ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; Functions to handle partitioning problems
; ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
(deffunction fix-pack (?pack)
    (return (matlabf PACK_fix ?pack)))

(deffunction rand-pack (?n)
    (bind ?pack (create$ 1))
    (for (bind ?i 2) (<= ?i ?n) (++ ?i)
        (bind ?pack (append$ ?pack (rand-int (+ 1 (max$ ?pack))))))
    (return ?pack)
    )

(deffunction pack-to-subsets (?pack)
    (bag delete my-bag)
    (bind ?*sets* (bag create my-bag))
    (for (bind ?i 1) (<= ?i (length$ ?pack)) (++ ?i)
        (bind ?el (nth$ ?i ?pack))
        (bind ?sat (bag get ?*sets* ?el))
        ;(printout t "i = " ?i " el = " ?el " sat = " ?sat crlf)
        (if (eq ?sat nil) then (bag set ?*sets* ?el (create$ ?i))
             else (bag set ?*sets* ?el (append$ ?sat ?i))))
    (return ?*sets*))
    
(deffunction get-large-subsets (?pack ?N)
    (bind ?subsets (pack-to-subsets ?pack))
    (bind ?indexes (create$ ))
    (bind ?n (call ?subsets size))
    (for (bind ?i 1) (<= ?i ?n) (++ ?i)
        (bind ?sat (bag get ?subsets ?i))
        (if (> (length$ ?sat) ?N) then (bind ?indexes (append$ ?indexes ?i)))
        )
    (return ?indexes)
    )

(deffunction get-small-subsets (?pack ?N)
    (return (complement$ (get-large-subsets ?pack ?N) ?pack)))

(deffunction has-large-subset (?pack ?N)
    (return (> (length$ (get-large-subsets ?pack ?N)) 0))
    )

(deffunction has-2-small-subsets (?pack ?N)
    (return (> (length$ (get-small-subsets ?pack ?N)) 1))
    )

(deffunction get-random-large-subset (?pack ?N)
    (return (rand-elem$ (get-large-subsets ?pack ?N)))
    )

(deffunction get-2-random-small-subsets (?pack ?N)
    (bind ?small (get-small-subsets ?pack ?N))
    (bind ?x1 (rand-elem$ ?small))
    (bind ?x2 (get-random-missing-element ?x1 ?small))
    (return (create$ ?x1 ?x2))
    )

(deffunction subsets-to-pack (?subsets ?ne)
    (bind ?pack (ones$ ?ne))
    (bind ?ns (call ?subsets size))
    (for (bind ?i 1) (<= ?i ?ns) (++ ?i)
        (bind ?sat (bag get ?subsets ?i))
        (foreach ?el ?sat 
            (bind ?pack (replace$ ?pack ?el ?el ?i)))
        )
    (return ?pack)
    )

(deffunction breakdown-subset (?pack ?index)
    (bind ?sets (pack-to-subsets ?pack))
    (bind ?sat (bag get ?sets ?index))
    (bind ?el (rand-elem$ ?sat))
    (bag set ?sets ?index (remove$ ?sat ?el))
    (bag set ?sets (+ 1 (call ?sets size)) (create$ ?el))
    (return (fix-pack (subsets-to-pack ?sets (length$ ?pack))))
    )

(deffunction merge-subsets (?pack ?indexes)
    (bind ?rem-cons (max$ ?indexes))
    (return (replace-all$ ?pack ?rem-cons (min$ ?indexes)))
    )