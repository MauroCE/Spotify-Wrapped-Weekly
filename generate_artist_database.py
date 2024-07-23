import pickle

artist_genres = {
    '0t3QQl52F463sxGXb1ckhB': ['australian dance', 'dance pop', 'electropop', 'metropopolis'],  # Betty Who
    '0IVWeUVFPCMT7MmhvqmfUr': [],                                                               # clear eyes
    '0PxzGnCYBpSuaI49OR94cA': [],                                                               # Big Wild
    '4oc6eCUAzc3EcutZmmAg5y': ['uk contemporary r&b'],                                          # Mullally
    '1bqxdqvUtPWZri43cKHac8': ['singer-songwriter pop', 'viral pop'],                           # MAX
    '5JZ7CnR6gTvEMKX4g70Amv': ['pop'],                                                          # Lauv
    '2vf4pRsEY6LpL5tKmqWb64': ['uk dance'],                                                     # Elderbrook
    '5LHRHt1k9lMyONurDHEdrp': ['hip hop', 'pop rap', 'rap', 'trap'],                            # Tyga
    '07YZf4WDAMNwqr4jfgOZ8y': ['dance pop', 'pop'],                                             # Jason Derulo
    '6nS5roXSAGhTGr34W6n7Et': ['edm', 'house', 'indietronica', 'uk dance'],                     # Disclosure
    '6bWxFw65IEJzBYjx3SxUXd': ['downtempo', 'electronica', 'trip hop'],                         # Morcheeba
    '6AMd49uBDJfhf30Ak2QR5s': ['new jersey underground rap', 'trap queen'],                     # Coi Leray
    '29WzbAQtDnBJF09es0uddn': ['british soul', 'neo soul', 'pop soul', 'soul'],                 # Corinne Bailey Rae
    '28WNtilgFPn1mdz3h0FjHl': [],                                                               # Mackenzy Mackay
    '0xndnh5xDy0nc1h6jwyzyO': [],                                                               # Becoming Young
    '3gTb0Vm6wFbRFVTAhDTgId': ['nashville hip hop', 'tennessee hip hop'],                       # Daisha McBride
    '3AuMNF8rQAKOzjYppFNAoB': ['atl hip hop', 'dance pop', 'hip pop', 'r&b', 'urban contemporary'],  # Kelly Rowland
    '6XyY86QOPPrYVGvF9ch6wz': ['alternative metal', 'nu metal', 'post-grunge', 'rap metal', 'rock'],  # Linkin Park
    '2ih5M0aTrQ97JX1nZuxDQY': ['high vibe'],                                                    # Iniko
    '5xuNBZoM7z1Vv8IQ6uM0p6': ['dance pop', 'pop', 'post-teen pop'],                            # JoJo
    '0lax1ZgWclW6mZFaGu27MM': ['kids dance party'],                                             # Cupid
    '4iHNK0tOyZPYnBU7nGAgpQ': ['dance pop', 'pop', 'urban contemporary'],                       # Mariah Carey
    '4xls23Ye9WR9yy3yYMpAMm': ['blues', 'rock-and-roll', 'rockabilly', 'soul'],                 # Little Richard
    '2Mu5NfyYm8n5iTomuKAEHl': ['alternative r&b', 'conscious hip hop', 'hip hop', 'neo soul', 'new jersey rap', 'r&b', 'soul'],  # Ms. Lauryn Hill
    '5EvFsr3kj42KNv97ZEnqij': ['pop rap', 'reggae fusion'],                                     # Shaggy
    '0TImkz4nPqjegtVSMZnMRq': ['atl hip hop', 'contemporary r&b', 'dance pop', 'girl group', 'hip pop', 'r&b', 'urban contemporary'],  # TLC
    '2NdeV5rLm47xAvogXrYhJX': ['dance pop', 'hip pop', 'pop', 'r&b', 'urban contemporary'],     # Ciara
    '586uxXMyD5ObPuzjtrzO1Q': ['edm'],                                                          # Sofi Tukker
    '77faXTf6wXs3L2CVol0c8C': ['classic hardstyle', 'euphoric hardstyle', 'rawstyle', 'xtra raw'],  # E-Force
    '5yw4tA8D5uG7tT3NaDvq10': ['social media pop'],                                             # Stellar
    '6WFDpw4u23uSpon4BHvFRn': ['uk pop'],                                                       # Cat Burns
    '6KImCVD70vtIoJWnq6nGn3': ['pop']                                                          # Harry Styles
}

with open("genres_by_artistid.pkl", "wb") as file:
    pickle.dump(artist_genres, file)
