from kivy.core.audio import SoundLoader

die_images = {
    1: 'images/1_dots.png',
    2: 'images/2_dots.png',
    3: 'images/3_dots.png',
    4: 'images/4_dots.png',
    5: 'images/5_dots.png',
    6: 'images/6_dots.png',
}

tables = {
    1: 'images/tabletop1.jpg',
    2: 'images/tabletop2.jpg',
    3: 'images/tabletop3.jpg',
    4: 'images/tabletop4.jpg',
    5: 'images/tabletop5.jpg',
    6: 'images/tabletop6.jpg'
}

sound_1 = SoundLoader.load('sounds/sound1.wav')
sound_2 = SoundLoader.load('sounds/sound2.wav')
sound_3 = SoundLoader.load('sounds/sound3.wav')
sound_4 = SoundLoader.load('sounds/sound4.wav')
sound_5 = SoundLoader.load('sounds/sound5.wav')
sound_6 = SoundLoader.load('sounds/sound6.wav')

sounds = {
    1: sound_1,
    2: sound_2,
    3: sound_3,
    4: sound_4,
    5: sound_5,
    6: sound_6
}

basket = 'images/basket.jpg'
