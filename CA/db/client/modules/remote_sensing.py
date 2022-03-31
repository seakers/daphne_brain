from client.modules.AbstractBuilder import AbstractBuilder

def get_module():

    status = {
        'color': '#E65100',
        'text': 'beta'
    }

    builder = AbstractBuilder('mdi-telescope', ['Remote Sensing'], 'Space Training 101', None)

    builder.add_slide('DODS_0')
    builder.add_slide('DODS_1')
    builder.add_slide('DODS_2')
    builder.add_slide('DODS_3')

    builder.add_mc_question(
        'What is the difference between active and passive remote sensing instruments?',
        [
            {'text': 'A. Active instruments are on all the time, passive instruments are only on part of the time', 'correct': False, 'id': 0},
            {'text': 'B. Passive instruments emit no electromagnetic radiation, while active instruments do', 'correct': True, 'id': 1},
            {'text': 'C. Active instruments will gimbal themselves to a target, passive ones will not', 'correct': False, 'id': 2},
            {'text': 'D. All of the above', 'correct': False, 'id': 3}
        ],
        'The correct answer is B, active instruments emit radiation and measure the amount that is reflected. Passive instruments emit no radiation',
        ['Remote Sensing']
    )

    builder.add_slide('DODS_4')  # EM Spectrum
    builder.add_slide('DODS_5')
    builder.add_slide('DODS_6')
    builder.add_slide('DODS_7')  # Path of Imaging
    builder.add_slide('DODS_8')  # Key EO/IR Parameters


    builder.add_mc_question(
        'A novel EO/IR imager is flying at 400km altitude where the onboard imager has an aperture diameter of D=5cm and operates at wavelength lambda=740nm. What is the resolution of the instrument?',
        [
            {'text': 'A. 500',
             'correct': False, 'id': 0},
            {'text': 'B. 200',
             'correct': True, 'id': 1},
            {'text': 'C. 300',
             'correct': False, 'id': 2},
            {'text': 'D. None of the above', 'correct': False, 'id': 3}
        ],
        'Explanation for maths',
        ['Remote Sensing']
    )

    builder.add_tf_question(
        'An instrument with a larger field of view will always have a larger swatch regardless of any other parameters.',
        False,
        'The correct answer is false, as swath is a function of both field of view and altitude. One instrument might have a larger field of view, but if it is flying very low it will have a smaller swath',
        ['Remote Sensing']
    )

    builder.add_slide('DODS_9')  # EO/IR Types
    builder.add_slide('DODS_10')
    builder.add_slide('DODS_11')
    builder.add_slide('DODS_12')
    builder.add_slide('DODS_13')
    builder.add_slide('DODS_14')

    builder.add_tf_question(
        'The more pixels an instrument\'s focal plane array has, the finer its resolution.',
        True,
        'This is true',
        ['Remote Sensing']
    )

    builder.add_tf_question(
        'Different wavelengths in the EM spectrum will react differently to phenomena.',
        True,
        'This is true. For example, Ka band wavelengths see more attenuation due to rain than others',
        ['Remote Sensing']
    )

    return builder.get_module()







