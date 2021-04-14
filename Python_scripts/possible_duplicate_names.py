
#======================================================================================
# Program:      Research for Improving the Systems of Education (RISE) in Nigeria
# Project:      Mission School Project
# Task:         Detecting supected duplicate names in the data
# Institution:  African School of Economics
# Consultant:   Henri Noël Kengne, Junior Data Scientist
# Superviser: Dr.Gabor Nyeki, Assistant Professor at the African School of Economics
#======================================================================================

# WE START BY IMPORTING THE NECESSARY MODULES WE WILL NEED
import pylev
import pandas as pd
import networkx as nx
import os

# SETTING THE WORKING DIRECTORY WITH NECESSARY SUBDIRECTORIES
main_directory = 'C:/Users/PT WORLD/Desktop/My Projects/RISE_mission_school_suspected_duplicates/'
os.chdir(main_directory)

newpath = r'./output_data'  # store figures here
if not os.path.exists(newpath):
    os.makedirs(newpath)


# SIMILARITY TOWS WORDS IN THE CASE WHERE 1 WORD IS AT MOST 1 LETTER LONGER THAN THE OTHER.
def one_extra_word(words_1, words_2):
    if abs(len(words_1) - len(words_2)) != 1:
        return False

    if len(words_1) > len(words_2):
        longer, shorter = words_1, words_2
    else:
        longer, shorter = words_2, words_1

    for k in range(len(longer)):
        longer_without_k = longer[:k] + longer[k + 1:]

        if longer_without_k == shorter:
            return True

    return False

# TESTING
assert not one_extra_word("foo".split(), "bar".split())
assert one_extra_word("foo".split(), "foo bar".split())
assert not one_extra_word("foo".split(), "foo bar baz".split())
assert not one_extra_word("foo bar".split(), "foo baz".split())

# ARE THE TWO WORDS MADE UP OF THE SAME LETTERS?
def same_words(words_1, words_2):
    return sorted(words_1) == sorted(words_2)


def similar_words_permissive(words_1, words_2):
    if same_words(words_1, words_2):
        return True
    else:
        return one_extra_word(words_1, words_2)


def similar_words_strict(words_1, words_2):
    if len(words_1) < 2 or len(words_2) < 2:           
        return same_words(words_1, words_2)
    return similar_words_permissive(words_1, words_2)


def split_at_nee(words):
    if "nee" not in words:
        return words, []

    return words[:words.index("nee")], words[words.index("nee") + 1:]


assert split_at_nee(["foo", "bar"])               == (["foo", "bar"], [])
assert split_at_nee(["foo", "bar", "nee", "baz"]) == (["foo", "bar"], ["baz"])


def swap_if_only_maiden_name(just_name, maiden_name):
    if not just_name and maiden_name:
        return maiden_name, []

    return just_name, maiden_name


assert swap_if_only_maiden_name([], [1]) == ([1], [])
assert swap_if_only_maiden_name([2], [1]) == ([2], [1])
assert swap_if_only_maiden_name([2], []) == ([2], [])


def string_distance_between_words(words_1, words_2):
    return pylev.levenshtein(" ".join(words_1), " ".join(words_2))


def similar_just_names_permissive(just_name_1, just_name_2):
    return (string_distance_between_words(
                just_name_1, just_name_2) <= 2
            or similar_words_permissive(just_name_1, just_name_2))


def similar_just_names_strict(just_name_1, just_name_2):
    if len(just_name_1) < 2 or len(just_name_2) < 2:
        cutoff = 1
    else:
        cutoff = 2

    return (string_distance_between_words(
                just_name_1, just_name_2) <= cutoff
            or similar_words_strict(just_name_1, just_name_2))


def similar_names_skeleton(name_1, name_2, similar_just_names_function):
    words_1, words_2 = name_1.lower().split(), name_2.lower().split()

    # just_name_1, maiden_name_1 = swap_if_only_maiden_name(
    #     split_at_nee(words_1))
    # just_name_2, maiden_name_2 = swap_if_only_maiden_name(
    #     split_at_nee(words_2))
    just_name_1, maiden_name_1 = split_at_nee(words_1)
    just_name_2, maiden_name_2 = split_at_nee(words_2)

    if not (maiden_name_1 and maiden_name_2):
        return similar_just_names_function(
                   just_name_1, just_name_2)

    return (string_distance_between_words(
                maiden_name_1, maiden_name_2) <= 2
            and similar_just_names_function(
                    just_name_1, just_name_2))


def similar_names_permissive(name_1, name_2):
    return similar_names_skeleton(
        name_1, name_2, similar_just_names_permissive)


def similar_names_strict(name_1, name_2):
    return similar_names_skeleton(
        name_1, name_2, similar_just_names_strict)

# LET US ASSERT DIFFERENT CASES
assert similar_names_permissive("foo", "foo nee baz")
assert similar_names_permissive("foo bar", "foo bar nee baz")
assert similar_names_permissive("foo bar nee bas", "foo bar nee baz")
assert similar_names_permissive("foo bar baz nee baz", "foo bar nee baz")
assert not similar_names_permissive("foo bar nee qwe", "foo bar nee baz")
assert not similar_names_permissive("foo bar baz nee baz", "foo bar qwe nee baz")
assert not similar_names_permissive("baz", "foo bar nee baz")

# TODO Add support for these: 
#assert not similar_names_permissive("foo baz", "foo bar nee baz")
#assert similar_names_permissive("foo qwe", "foo bar nee qwe")
assert similar_names_permissive("foo bar baz", "foo bar nee baz")


assert not similar_names_strict(    "foo", "foo bar")
assert     similar_names_permissive("foo", "foo bar")


#for function in (similar_names, similarity_name):
for function in (similar_names_strict, similar_names_permissive):
    print(f"Testing {function.__name__}.")

    assert function("foo", "foo")
    assert function("foo bar", "foo bar")
    assert function("foo bar", "bar foo")
    assert function("foo bar", "foo baz bar")
    assert function("foo bar", "baz foo bar")
    assert function("foo bar", "foo bar baz")
    assert not function("foo", "bar")
    assert not function("foo", "foo bar baz")
    assert not function("foo bar", "qwe foo bar baz")
    assert not function("foo bar baz", "foo bar qwe")
    assert not function("foo bar", "baz bar foo")


def nodes_from_df(df):
    return tuple(
        (elrow["subject_id"], elrow["subject_name"])  # stripped_name
        for i, elrow in df.iterrows())


def graph_from_nodes(nodes):
    G = nx.Graph()
    for node in nodes:
        G.add_node(node)
    return G


def add_edges_skeleton(G, similar_names_function):
    for i_id, i_name in G.nodes():
        for j_id, j_name in G.nodes():
            if similar_names_function(i_name, j_name):
                G.add_edge(
                    (i_id, i_name),
                    (j_id, j_name))


def add_edges_permissive(G):
    return add_edges_skeleton(G, similar_names_permissive)


def add_edges_strict(G):
    return add_edges_skeleton(G, similar_names_strict)


def get_components(G):
    components = []

    for component in nx.connected_components(G):
        if len(component) <= 7:
            components.append(component)
        else:
            print(f"Breaking up component of {len(component)} elements:", component)
            sub_G = graph_from_nodes(component)
            add_edges_strict(sub_G)

            components.extend(
                list(nx.connected_components(sub_G)))

    return components

def main():
    # CONSTRUCTION OF THE STRIPPRD NAMES NETWORK
    
    # Loading in the data
    df = pd.read_csv("./Raw_Data/subject_ids_enugu_ogui_eke_2020-10-30.csv")


    G = graph_from_nodes(
            nodes_from_df(df))
    add_edges_permissive(G)

    # Visualization of the network
    # nx.draw_networkx(G)

    # for component in get_components(G):
    #      print(component)

    ###############################################
    # WE WANT TO PROVIDE THE OUTPUT ON A CSV FILE
    ###############################################

    # the list of the componets
    list_components = get_components(G)

    # Sort the list of the components with respect to the lenght of its elements.
    #sort_list_components = sorted(break_large_components(list_components), key=len, reverse = True)
    sort_list_components = sorted(list_components, key=len, reverse = True)

    # "Pythonic": expression that is idiomatic in Python.
    # lists of the subject ids in the same order as in sort_list_components
    similar_ids = dict(
        (subject_id, min(s_id for s_id, name in component))
        for component in sort_list_components
        for subject_id, name in component)

    # list of similar_subject ids.
    # df["similar_subject_id"] = [
    #     similar_ids[subject_id] for subject_id in df["subject_id"]]
    similar_subjet_id = [ similar_ids[subject_id] for subject_id in similar_ids]
    new_disposition_subjet_id = [ subject_id for subject_id in similar_ids]

    # Rearrange the rows of the dataframe based on the new order of the subject ids
    df.index = df['subject_id']
    data = df.reindex(new_disposition_subjet_id)
    data['similar_subject_id'] = similar_subjet_id
    
    # Save the output in a csv file
    data.to_csv("./output_data/output_duplicate_names_enugu_ogui_eke_2020-10-30.csv", index = False)
    
    print("Here are the sorted lists")
    for component in sort_list_components:
        print(component)

if __name__ == "__main__":
    main()

