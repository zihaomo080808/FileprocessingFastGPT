from preprocessing.html_html import html_to_html_fill

def main():
    simplified_html = "/Users/zihaomo/Downloads/AI填尽调报告/一个完整例子已填完/3.3 私募管理人及产品尽职调查问卷20221111 (1)_simplified_copy.txt"
    template_html = "/Users/zihaomo/Downloads/AI填尽调报告/一个完整例子已填完/3.3 私募管理人及产品尽职调查问卷20221111 (1)_with_comments.htm"
    output_html = "/Users/zihaomo/Downloads/AI填尽调报告/一个完整例子已填完/3.3 私募管理人及产品尽职调查问卷20221111 (1)_with_comments_with_comments_final_filled1.html"
    html_to_html_fill(simplified_html, template_html, output_html)

if __name__ == "__main__":
    main()