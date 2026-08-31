import re
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import sys

#Load the file
def load_report(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    print(f'loaded {filepath}')
    return content

#Extract ALL Slack values
def extract_slacks(sta_content):
    pattern = re.findall(r'Clock\s*:\s*(\S+).*?Slack\s*:\s*([\d.]+)', sta_content, re.DOTALL)
    labels = []
    slacks = []
    seen   = {}   
    for match in pattern:
        name  = match[0]
        slack = float(match[1])
        if name in seen:
            seen[name] += 1
            name = f'{name}\n(Hold)'    # second occurrence = Hold
        else:
            seen[name]  = 1
            name = f'{name}\n(Setup)'   # first occurrence = Setup
        labels.append(name)
        slacks.append(slack)
    return labels, slacks

#Extract ALL Resources used
def extract_synthesis(syn_content):
    pattern = re.findall(r';\s*([A-Za-z ]+?)\s*:\s*(\d+)\s*/\s*(\d+)', syn_content)
    resources = []
    for match in pattern:
        name = match[0].strip()
        used = int(match[1])
        total = int(match[2])
        percent = round((used/total)*100, 2)
        resources.append({'name': name, 'used': used, 'total': total, 'percent': percent})
    return resources

#Print Summaries
def print_sta_summary(slacks):
    wns = min(slacks)
    tns = sum(s for s in slacks if s < 0)
    print('\n'+'='*50)
    print('STA TIMING SUMMARY')
    print('='*50)
    print(f'All Slack Values (ns): {slacks}')
    print(f'Worst Negative Slack: {wns} ns')
    print(f'Total Negative Slack: {tns} ns')
    if wns >= 0:
        print('TIMING STATUS: PASSED')
    else:
        print('TIMING STATUS: FAILED')
    print('='*50)
def print_synthesis_summary(resources):
    print('\n'+'='*50)
    print('SYNTHESIS RESOURCE SUMMARY')
    print('='*50)
    for r in resources:
        status = 'Good' if r['percent'] < 80 else 'Too High'
        print(f"{r['name']:<20}{r['used']:>6}/"f"{r['total']:>6} {r['percent']:>5}% {status}")
    print('='*50)

#Generate a chart
def generate_chart(labels, slacks, resources):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize = (16, 6))
    fig.suptitle('EDA ANALYSIS SUMMARY', fontweight = 'bold', fontsize = 13)
    #Left panel
    colours = ['green' if s >= 0 else 'red' for s in slacks]
    bars1 = ax1.bar(labels, slacks, color = colours, edgecolor = 'black', width = 0.5)
    ax1.axhline(y = 0, color = 'black', linewidth = 1.2, linestyle = '--')
    ax1.set_ylim(0, max(slacks)*1.25)
    ax1.set_title('STA Slack by Clock Domain', fontweight = 'bold')
    ax1.set_ylabel('Slack (ns)')
    ax1.set_xlabel('Clock Domain')
    for bar, val in zip(bars1, slacks):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2, f'{val}ns', ha = 'center', va = 'center', fontsize = 9, color = 'white', fontweight = 'bold')
    pass_patch = mpatches.Patch(color = 'green', label = 'Timing Met')
    fail_patch = mpatches.Patch(color = 'red', label = 'Timing Violated')
    ax1.legend(handles = [pass_patch, fail_patch], loc = 'upper left', fontsize = 9)
    #Right panel
    res_labels = [r['name'] for r in resources]
    percentages = [r['percent'] for r in resources]
    colours2 = ['green' if p < 80 else 'red' for p in percentages]
    bars2 = ax2.barh(res_labels, percentages, color = colours2, edgecolor = 'black', height = 0.5)
    ax2.axvline(x = 80, color = 'red', linewidth = 1.2, linestyle = '--', label = '80% Threshold')
    ax2.set_xlim(0,100)
    ax2.set_title('Resource Utilisation', fontweight = 'bold')
    ax2.set_xlabel('Utilisation (%)')
    for bar, pct in zip(bars2, percentages):
        ax2.text(max(pct/2, 0.5), bar.get_y() + bar.get_height()/2, f'{pct}%', ha = 'center', va = 'center', fontsize = 9, color = 'white', fontweight = 'bold')
    under_patch = mpatches.Patch(color = 'green', label = 'Under 80%')
    over_patch = mpatches.Patch(color = 'red', label = 'Over 80%')
    ax2.legend(handles = [under_patch, over_patch], loc = 'lower right', fontsize = 9)
    plt.tight_layout()
    plt.savefig('eda_summary.png')
    plt.show()
    print('Chart saved as eda_summary.png')

def save_report(slacks, labels, resources):
    with open('eda_summary.txt', 'w') as f:
        f.write('EDA ANALYSIS SUMMARY\n')
        f.write('='*50 + '\n\n')
        f.write('STA TIMING SUMMARY\n')
        f.write('='*50 + '\n')
        for label, slack in zip(labels, slacks):
            slack = float(slack)
            status = 'PASS' if slack >= 0 else 'FAIL'
            label = label.replace('\n', '')
            f.write(f'{label:<30}{slack:>8.3f} ns {status}\n')
        f.write(f'\nWNS: {float(min(slacks)):.3f} ns\n')
        f.write(f'TNS: {float(sum(s for s in slacks if float(s) < 0)): 3f} ns\n\n')
        f.write('SYNTHESIS SUMMARY\n')
        f.write('='*50 + '\n')
        for r in resources:
            f.write(f"{str(r['name']):<20} {int(r['used']):>6}/{int(r['total']):>6}{float(r['percent']):>5}%\n")
    print('report saved as eda_summary.txt')
#Main
def main():
    sta_file = sys.argv[1] if len(sys.argv) > 1 else 'timing_report.rpt'
    syn_file = sys.argv[2] if len(sys.argv) > 2 else 'synthesis_report.rpt'
    #STA
    sta_content = load_report(sta_file)
    labels, slacks = extract_slacks(sta_content)
    print_sta_summary(slacks)
    #Synthesis
    syn_content = load_report(syn_file)
    resources = extract_synthesis(syn_content)
    print_synthesis_summary(resources)
    #Report
    save_report(slacks, labels, resources)
    #Chart
    generate_chart(labels, slacks, resources)

if __name__ == '__main__':
    main()


