from parsing.entity_extraction import extract_entities


if __name__ == '__main__':
    request_url = 'https://tjournal.ru/flood/567408-mechty-o-budushchem'

    entities = extract_entities(request_url)
    print(entities)
