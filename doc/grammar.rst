Vy Grammar
----------

Normal mode statement follow those rules:

- If starts with " 
    valid   (  "  )
    -> set next char as target register
      valid   (  "a_  )
    - If next char is an invalid register 
      invalid (  "£_  )
        -> loop to the top.

- If an numeric key in entered
  valid   (  "a1_  )
  valid   (  4_    )
    -> gather all numeric keys and treat them as a count
      valid   (  "a123_  )
      valid   (  234_    )

Here come the interresting part:

- If next key is neither a «stand alone command», nor a
  «motion», nor a «full command», nor the start of any.
    - > loop to the top !

- If next key is a «stand-alone command»
    -> Pass it the count, the register and execute it
    - if it return 'normal' or None
        - > loop to the top !
        - > otherwise return it.
        
- If next key is a «motion command»
    -> Execute it count times
    - if it return 'normal' or None
        - > loop to the top !
        - > otherwise return it.

- If next key is a «full command»:
    -> Jump to the weird part!

- If the key is the start of a multiple letter command
    -> adds it the next key press and jump to the interesting part

Here come the weird part:

