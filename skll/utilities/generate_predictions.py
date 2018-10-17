#!/usr/bin/env python
# License: BSD 3 clause
"""
Loads a trained model and outputs predictions based on input feature files.

:author: Dan Blanchard
:contact: dblanchard@ets.org
:organization: ETS
:date: February 2013
"""

from __future__ import absolute_import, print_function, unicode_literals

import argparse
import logging
import os
import sys

from skll.data.readers import EXT_TO_READER
from skll.learner import Learner
from skll.version import __version__


class Predictor(object):
    """
    A wrapper around a ``Learner`` instance to load models and get
    predictions for feature strings.
    """

    def __init__(self, model_path, threshold=None, positive_label=1,
                 return_all_probabilities=False, logger=None):
        """
        Initialize the predictor.

        Parameters
        ----------
        model_path : str
            Path to use when loading trained model.
        threshold : float, optional
            If the model we're using is generating probabilities
            of the positive label, return 1 if it meets/exceeds
            the given threshold and 0 otherwise.
            Defaults to ``None``.
        positive_label : int, optional
            If the model is only being used to predict the
            probability of a particular class, this
            specifies the index of the class we're
            predicting. 1 = second class, which is default
            for binary classification.
            Defaults to 1.
        return_all_probabilities: bool
            A flag indicating whether to return the probabilities for all
            labels in each row instead of just returning the probability of
            `positive_label`.
        logger : logging object, optional
            A logging object. If ``None`` is passed, get logger from ``__name__``.
            Defaults to ``None``.
        """
        # self.logger = logger if logger else logging.getLogger(__name__)
        self._learner = Learner.from_file(model_path)
        self._pos_index = positive_label
        self.threshold = threshold
        self.all_probs = return_all_probabilities
        self.output_file_header = None

    def predict(self, data):
        """
        Generate a list of predictions for the given examples.

        Parameters
        ----------
        data : skll.FeatureSet
            The ``FeatureSet`` instance to get predictions for.

        Returns
        -------
        A list of predictions generated by the model.
        """
        # compute the predictions from the learner
        preds = self._learner.predict(data)
        preds = preds.tolist()
        labels = self._learner.label_list

        # Create file header list, and transform predictions as needed
        # depending on the specified prediction arguments.
        if self._learner.probability:
            if self.all_probs:
                self.output_file_header = ["id"] + [str(x) for x in labels]
            elif self.threshold is None:
                label = self._learner.label_dict[self._pos_index]
                self.output_file_header = ["id",
                                           "Probability of '{}'".format(label)]
                preds = [pred[self._pos_index] for pred in preds]
            else:
                self.output_file_header = ["id", "prediction"]
                preds = [int(pred[self._pos_index] >= self.threshold)
                         for pred in preds]
        elif self._learner.model._estimator_type == 'regressor':
            self.output_file_header = ["id", "prediction"]
        else:
            self.output_file_header = ["id", "prediction"]
            preds = [labels[pred if isinstance(pred, int) else int(pred[0])]
                     for pred in preds]
        return preds


def main(argv=None):
    """
    Handles command line arguments and gets things started.

    Parameters
    ----------
    argv : list of str
        List of arguments, as if specified on the command-line.
        If None, ``sys.argv[1:]`` is used instead.
    """

    # Get command line arguments
    parser = argparse.ArgumentParser(
        description="Loads a trained model and outputs predictions based \
                     on input feature files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        conflict_handler='resolve')
    parser.add_argument('model_file',
                        help='Model file to load and use for generating \
                              predictions.')
    parser.add_argument('input_file',
                        help='A csv file, json file, or megam file \
                              (with or without the label column), \
                              with the appropriate suffix.',
                        nargs='+')
    parser.add_argument('-i', '--id_col',
                        help='Name of the column which contains the instance \
                              IDs in ARFF, CSV, or TSV files.',
                        default='id')
    parser.add_argument('-l', '--label_col',
                        help='Name of the column which contains the labels\
                              in ARFF, CSV, or TSV files. For ARFF files, this\
                              must be the final column to count as the label.',
                        default='y')
    parser.add_argument('-p', '--positive_label',
                        help="If the model is only being used to predict the \
                              probability of a particular label, this \
                              specifies the index of the label we're \
                              predicting. 1 = second label, which is default \
                              for binary classification. Keep in mind that \
                              labels are sorted lexicographically.",
                        default=1, type=int)
    parser.add_argument('-q', '--quiet',
                        help='Suppress printing of "Loading..." messages.',
                        action='store_true')
    parser.add_argument('--output_file', '-o',
                        help="Path to output tsv file. If not specified, "
                             "predictions will be printed to stdout.")
    parser.add_argument('--version', action='version',
                        version='%(prog)s {0}'.format(__version__))
    probability_handling = parser.add_mutually_exclusive_group()
    probability_handling.add_argument('-t', '--threshold',
                                      help="If the model we're using is "
                                           "generating probabilities of the "
                                           "positive label, return 1 if it "
                                           "meets/exceeds the given threshold "
                                           "and 0 otherwise.",  type=float)
    probability_handling.add_argument('--all_probabilities', '-a',
                                      action='store_true',
                                      help="Flag indicating whether to output "
                                           "the probabilities of all labels "
                                           "instead of just the probability "
                                           "of the positive label.")

    args = parser.parse_args(argv)

    # Make warnings from built-in warnings module get formatted more nicely
    logging.captureWarnings(True)
    logging.basicConfig(format=('%(asctime)s - %(name)s - %(levelname)s - ' +
                                '%(message)s'))
    logger = logging.getLogger(__name__)

    if args.positive_label and args.all_probabilities:
        logger.warning("Ignoring `--positive_label` since "
                       "`--all_probabilities` is set to True. The probability "
                       "of all labels will be displayed.")

    # Create the classifier and load the model
    predictor = Predictor(args.model_file,
                          positive_label=args.positive_label,
                          threshold=args.threshold,
                          return_all_probabilities=args.all_probabilities,
                          logger=logger)

    # Iterate over all the specified input files
    for i, input_file in enumerate(args.input_file):

        # make sure each file extension is one we can process
        input_extension = os.path.splitext(input_file)[1].lower()
        if input_extension not in EXT_TO_READER:
            logger.error(('Input file must be in either .arff, .csv, '
                          '.jsonlines, .libsvm, .megam, .ndj, or .tsv format. '
                          ' Skipping file {}').format(input_file))
            continue
        else:
            # Iterate through input file and collect the information we need
            reader = EXT_TO_READER[input_extension](input_file,
                                                    quiet=args.quiet,
                                                    label_col=args.label_col,
                                                    id_col=args.id_col)
            feature_set = reader.read()
            preds = predictor.predict(feature_set)
            header = predictor.output_file_header

            if args.output_file is not None:
                with open(args.output_file, "a") as fout:
                    if i == 0:  # Only write header once per set of input files
                        print("\t".join(header), file=fout)
                    if args.all_probabilities:
                        for i, probabilities in enumerate(preds):
                            id_ = feature_set.ids[i]
                            probs_str = "\t".join([str(p) for p in probabilities])
                            print("{}\t{}".format(id_, probs_str), file=fout)
                    else:
                        for i, pred in enumerate(preds):
                            id_ = feature_set.ids[i]
                            print("{}\t{}".format(id_, pred), file=fout)
            else:
                if i == 0:  # Only write header once per set of input files
                    print("\t".join(header))
                if args.all_probabilities:
                    for i, probabilities in enumerate(preds):
                        id_ = feature_set.ids[i]
                        probs_str = "\t".join([str(p) for p in probabilities])
                        print("{}\t{}".format(id_, probs_str))
                else:
                    for i, pred in enumerate(preds):
                        id_ = feature_set.ids[i]
                        print("{}\t{}".format(id_, pred))


if __name__ == '__main__':
    main()
