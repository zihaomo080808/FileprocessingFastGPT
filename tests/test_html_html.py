from preprocessing.html_html import html_to_html_fill

def main():
    simplified_html = "/Users/zihaomo/Downloads/AI填尽调报告/未填的尽调报告/机构新format/东方财富证券私募类资产管理机构尽职调查报告（XXXX资产管理有限公司）-管理人提供_simplified_copy.txt"
    template_html = "/Users/zihaomo/Downloads/AI填尽调报告/未填的尽调报告/机构新format/东方财富证券私募类资产管理机构尽职调查报告（XXXX资产管理有限公司）-管理人提供.htm"
    output_html = "/Users/zihaomo/Downloads/AI填尽调报告/未填的尽调报告/机构新format/东方财富证券私募类资产管理机构尽职调查报告（XXXX资产管理有限公司）-管理人提供_final_filled2.html"
    html_to_html_fill(simplified_html, template_html, output_html)

if __name__ == "__main__":
    main()