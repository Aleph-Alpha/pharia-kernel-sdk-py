.. pharia_kernel_sdk_py documentation master file, copied from aleph_alpha client
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Pharia Kernel SDK Python documentation!
==================================================

Python SDK for the `Pharia Kernel`_ .

Usage
-----

Simple Example

.. code:: python

      from pharia_skill import ChatParams, Csi, Message, skill
      from pydantic import BaseModel


      class Input(BaseModel):
         topic: str


      class Output(BaseModel):
         haiku: str


      @skill
      def run(csi: Csi, input: Input) -> Output:
         system = Message.system("You are a poet who strictly speaks in haikus.")
         user = Message.user(input.topic)
         params = ChatParams(max_tokens=64)
         response = csi.chat("llama-3.1-8b-instruct", [system, user], params)
         return Output(haiku=response.message.content.strip())



.. toctree::
   :maxdepth: 4
   :caption: Contents:

   modules


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

.. _Pharia Kernel: https://pharia-kernel.aleph-alpha.stackit.run
