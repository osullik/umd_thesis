# Final Presentation Details: 

[Presentation (Google Slides)](https://docs.google.com/presentation/d/1YWhL36Z9ZoBPv68LdjC0d5L7LNzelYCr1r33VaAmhCU/edit?usp=sharing)

# LaTeX Compilation Instructions

## Prepare the environment 

### Setting up compilation environment for MacOS: 

1. Download [Homebrew](brew.sh): 

        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

2. Install TexLive: 

        brew install texlive

3. Install Inkscape

        brew install --cask inkscape

4. (If it isn't on your machine by default) GNU Make

        brew install make

### Setting up comilation environment For Windows: 

1. Run Powershell as administrator: 

2. Install [Chocolatey](https://chocolatey.org/): 

        Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

3. Install GNU Make: 

        choco install Make

4. Install Perl (for LatexMk)

        choco install strawberryperl

5. Install Ruby (for Editing Scripts)

        choco install ruby

6. Install TexLive Utilites: 

        choco install texlive

7. Install MikTex: 

        choco install miktex

8. Install LatexMK with MikTex Package Manager (through GUI)

9. Install InkScape

        choco install inkscape


## Compile the file: 

To compile the PDF, simply run the following from the root of the **dissertation** directory:

    make thesis.pdf

You'll notice a lot of random intermediary files get made. To get rid of them and leave your PDF use:

    make publish

Sometimes everything goes wrong and we need to start again, when that happens use: 

    make clean

The scripts directory contains a lot of [Jordan's](https://github.com/Pinafore/publications/tree/master/scripts) useful editing and checking scripts. Github tends to mess with the permissions on these, so you'll likely need to CHMOD them back to be executable again. The *make thesis.pdf* command uses some of these scripts, so it is a good idea to do that occasionally. 

# Project Structure:

```
├── README.md
├── bibliography
│   ├── summer2023.bib
│   └── summer2023.bib.sav
├── dissertation
│   ├── Figures
│   ├── Reference
│   │   └── 99_Lit_Review_Raw.tex
│   ├── Scripts
│   │   ├── -h.tex
│   │   ├── acl_formatchecker.py
│   │   ├── camera_copy.sh
│   │   ├── clean_bib.py
│   │   ├── dictionary.txt
│   │   ├── diff.py
│   │   ├── hunspell_dictionary.dic
│   │   ├── latex2txt.py
│   │   ├── latex_deps.py
│   │   ├── latex_lines.py
│   │   ├── latex_lines_test.py
│   │   ├── merge_bibtex.py
│   │   ├── output.tex
│   │   ├── preamble_check.py
│   │   ├── rscript_if_ne.sh
│   │   ├── sanitize.py
│   │   ├── sanitizeBib.py
│   │   ├── spell.py
│   │   ├── split_pdf.py
│   │   ├── start_paper.py
│   │   ├── style-censor
│   │   ├── style-check
│   │   │   ├── bad-words
│   │   │   ├── barrass
│   │   │   ├── common-typos
│   │   │   ├── day-gastel
│   │   │   ├── foolish-phrases
│   │   │   ├── latex-checking
│   │   │   ├── misspellings
│   │   │   ├── my-rules
│   │   │   ├── networking-research
│   │   │   ├── passive-voice
│   │   │   └── verbose-phrases
│   │   ├── style-check.rb
│   │   ├── styleCheckResults.txt
│   │   ├── test.tex
│   ├── Sections
│   │   ├── 00_Abstract.tex
│   │   ├── 01_Titlepage.tex
│   │   ├── 02_Copyright.tex
│   │   ├── 03_Preface.tex
│   │   ├── 04_Foreword.tex
│   │   ├── 05_Dedication.tex
│   │   ├── 06_Acknowledgements.tex
│   │   ├── 07_Abbreviations-supertabular.tex
│   │   ├── 10_Introduction.tex
│   │   ├── 11_Intelligence_Security_Context.tex
│   │   ├── 12_Graph_Data_Structures.tex
│   │   ├── 13_Graph_Hardware_Acceleration.tex
│   │   ├── 14_Benchmarking_Graphs.tex
│   │   ├── 15_Thesis_Outline.tex
│   │   ├── 20_Related_Work.tex
│   │   ├── 30_Graph_Hardware_Benchmarking.tex
│   │   ├── 31_GHA_Problem_Statement.tex
│   │   ├── 32_GHA_Methodology.tex
│   │   ├── 33_GHA_Design.tex
│   │   ├── 34_GHA_Results.tex
│   │   ├── 35_GHA_Discussion.tex
│   │   ├── 40_Community_Detection_Case_Study.tex
│   │   ├── 41_CD_Problem_Statement.tex
│   │   ├── 42_CD_Methodology.tex
│   │   ├── 43_CD_Design.tex
│   │   ├── 44_CD_Results.tex
│   │   ├── 45_CD_Discussion.tex
│   │   ├── 50_Conclusion.tex
│   │   ├── 51_Future_Work.tex
│   │   ├── 52_Conclusion.tex
│   │   └── AppendixA.tex
│   ├── Style
│   │   ├── cite.sty
│   │   ├── floatrow.sty
│   │   ├── indentfirst.sty
│   │   ├── latexsym.sty
│   │   ├── listings.sty
│   │   ├── longtable.sty
│   │   ├── lscape.sty
│   │   ├── ltcaption.sty
│   │   ├── macros.tex
│   │   ├── microtype.sty
│   │   ├── multirow.sty
│   │   ├── setspace.sty
│   │   ├── slashbox.sty
│   │   ├── supertabular.sty
│   │   ├── tabls.sty
│   │   ├── thesis-2.cls
│   │   ├── thesis.cls
│   │   ├── titlesec.sty
│   │   ├── tocloft.sty
│   │   └── url.sty
│   ├── makefile
│   ├── thesis.pdf
│   └── thesis.tex
```