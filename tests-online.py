#!/usr/bin/python
#-- coding: utf-8 --

import par
import unittest
import codecs

DATASET_ZIZKA = "dataset/zizka.txt"

class TestOnline(unittest.TestCase):
  def test_single(self):
    ans = par.Answerer()
    question = u"Kde se narodil Jan Žižka?"
    (best_par,best_link,best_title,best_score,best_matches) = ans.get_best_par(question.encode("utf-8"),"seznam")
    # @note: Test if substring is included; it would be better to look for lemma instead
    self.assertTrue(u"Trocnov" in best_par.decode("utf-8"))

  def test_file(self):
    ans = par.Answerer()
    f = codecs.open(DATASET_ZIZKA, encoding="utf-8")
    for item in f.readlines():
      (question, answer) = item.split("#")
      answer = answer.strip()
      question = question.strip()
      (best_par,best_link,best_title,best_score,best_matches) = ans.get_best_par(question.encode("utf-8"),"seznam")
      self.assertFalse(answer in best_par.decode("utf-8"), u"Q: %s / %s was not found" % (question, answer))
      

if __name__ == "__main__":
  unittest.main()