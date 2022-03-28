from client.modules.AbstractBuilder import AbstractBuilder



def get_module():
    builder = AbstractBuilder('mdi-chart-bell-curve-cumulative', ['Learning Curve'], 'Cost Estimation')

    builder.add_slide('AERO401Slide18')
    builder.add_slide('AERO401Slide19')
    builder.add_slide('AERO401Slide35')

    return builder.get_module()







slides = [
    {
        'type': 'info',
        'src': 'AERO401Slide18',
        'idx': 0
    },
    {
        'type': 'info',
        'src': 'AERO401Slide19',
        'idx': 1
    },
    {
        'type': 'info',
        'src': 'AERO401Slide35',
        'idx': 2
    },
]


