from cube.api import Cube
import random
import copy


def modify_data(data_dict, include_adversarial, include_contrast, include_negation):

    # Initialize the parser
    cube=Cube(verbose=True)
    cube.load("en")

    data_length = len(data_dict)
    
    # Allocate different data for each type
    # Not actually needed, just used to show which data we are not using
    # default = data_dict[:(data_length // 4)]
    # # Will contain the training samples for adversarial data
    # adversarial = data_dict[(data_length // 4 + 1): (data_length * 2 // 4 )]
    # # Will contain the training samples for contrast data
    # contrast = data_dict[(data_length * 2 // 4 + 1): (data_length * 3 // 4 )]
    # # Will contain the training samples for negation data
    # negation = data_dict[(data_length  * 3 // 4 + 1):]

    # Allocate the same data for each type
    bool_array = [True, include_adversarial, include_contrast, include_negation]
    num_partitions = len(bool_array)
    default, adversarial, contrast, negation = [], [], [], []
    default = data_dict[:(data_length // num_partitions)]
    if include_adversarial:
        adversarial = copy.deepcopy(default)
    if include_contrast:
        contrast = copy.deepcopy(default)
    if include_negation:
        negation = copy.deepcopy(default)


    # Modifying to adversarial data
    for example in adversarial:
        # Get two random sentences
        sentences = example['context'].split('.')
        num_sentences = len(sentences)
        first = sentences[random.randint(0, num_sentences // 2)]
        second = sentences[random.randint(num_sentences // 2 + 1, num_sentences - 1)]
        # Parse each sentence for prepositions, and add them to the question
        parsed = cube(first)
        # Get random prep phrase
        first_prep_phrase= get_tag(parsed, 'ADP')

        parsed = cube(second)
        # Get random prep phrase
        second_prep_phrase = get_tag(parsed, 'ADP')
        
        # Modify question
        a_question = example['question'][0:-1] + first_prep_phrase + second_prep_phrase + '?'
        example['question'] = a_question
        # Answer will be N/A
        example['answers'] = None

    # Modifying to contrast data
    for example in contrast:
        
        parsed = cube[example['question']]

        propn = get_tag(parsed, 'PROPN')
        if propn is None:
            propn = get_tag(parsed, 'NNP')

        sentences = example['context'].split('.')

        # Find all prep phrases with the noun in it
        prep_phrase = ''
        for sentence in sentences:
            if sentence.index(propn):
                parsed = cube(sentence)
                prep_phrase = prep_phrase + ' ' + get_tag(parsed, 'ADP')

        # Modify the question
        c_question = example['question'][0:-1] + prep_phrase + '?'
        example['question'] = c_question
        # Answer will remain same, even with extra qualifiers

    for example in negation:
        question = example['question']
        # Find the root of question
        root = ''
        parsed = cube(question)
        for pos in parsed.sentences[0].words:
            if str(pos.label) == 'root':
                root = pos.word

        # Will always exist
        root_index = question.find(root)

        # Find the first verb in the question, change it to start of question
        first_verb = get_tag(parsed, 'AUX')

        verb_index = question.find(first_verb)

        # Sometimes add not, if added, answer becomes No
        add_not = random.randint(0, 1)
        n_question = ''
        if add_not or verb_index >= root_index:
            n_question = question[verb_index:root_index] + " not " + question[root_index:]
            example['answers'] = {'text':'no'}
        else:
            n_question = question[verb_index:]
            example['answers'] = {'text':'yes'}
    
        example['question'] = n_question

    return default + adversarial + contrast + negation

# Will return the first word or words with the tag
# If it is a preposition, it will return the prepositional phrase
def get_tag(parsed_sentence, tag):
    word = None
    word_index = 0

    for index, pos in enumerate(parsed_sentence.sentences[0].words):
        if pos.upos == tag or pos.xpos == tag:
            if word is None:
                word = pos.word
            else:
                # For compound POS
                word = word + ' ' + pos.word
        if pos.upos == 'ADP':
            # want to find prepositional phrase
            while parsed_sentence.sentences[0].words[word_index].xpos != 'NNP':
                word = word + ' ' + parsed_sentence.sentences[0].words[word_index].word
                word_index += 1
            # Change tag to nnp and it will keep adding it until it finds a different part of speech
            tag = 'NNP'
    return word