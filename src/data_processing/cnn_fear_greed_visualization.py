def create_gauge(self, value=None):
    """반원형 Fear & Greed 게이지 생성 (0-180도 균등 분포)"""
    if value is None:
        value = self.df['value'].iloc[-1]
        
    status, color = self.get_status(value)

    # 플롯 설정
    fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(111, projection='polar')
    
    # 반원형으로 수정 (0-180도)
    theta = np.linspace(0, np.pi, 100)
    
    # 배경 설정
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    # 세그먼트 생성 (전체 180도에 균등 분포)
    boundaries = [0, 25, 45, 55, 75, 100]
    labels = ['Extreme\nFear', 'Fear', 'Neutral', 'Greed', 'Extreme\nGreed']
    
    # 각 세그먼트의 각도 계산
    angles = np.array(boundaries) * np.pi / 100

    # 세그먼트 그리기
    for i, (start, end, label) in enumerate(zip(angles[:-1], angles[1:], labels)):
        mask = (theta >= start) & (theta <= end)
        color = list(self.colors.values())[i]
        
        # 세그먼트 채우기
        ax.fill_between(theta[mask], 0.5, 0.9, 
                       color=color, alpha=0.6)
        
        # 레이블 위치 조정
        mid_angle = (start + end) / 2
        label_radius = 1.0  # 레이블 위치 조정
        
        # 레이블 회전 조정
        rotation = np.rad2deg(mid_angle)
        if rotation > 90:
            rotation = rotation - 180
            
        ax.text(mid_angle, label_radius, label,
               ha='center', va='center',
               rotation=rotation,
               fontsize=10, fontweight='bold')

    # 눈금 제거
    ax.set_rticks([])
    
    # 값 눈금 추가 (0, 25, 50, 75, 100)
    ax.set_xticks(np.array([0, 25, 50, 75, 100]) * np.pi / 100)
    ax.set_xticklabels(['0', '25', '50', '75', '100'])
    
    # 바늘 그리기
    needle_angle = value * np.pi / 100
    ax.plot([needle_angle, needle_angle], [0, 0.7], 
            'k-', linewidth=2, zorder=5)
    
    # 현재 값 표시
    ax.text(np.pi/2, 0.3, f'{int(value)}',
            ha='center', va='center',
            fontsize=30, fontweight='bold')
    ax.text(np.pi/2, 0.2, status,
            ha='center', va='center',
            fontsize=14, color=color)

    # 불필요한 부분 제거 및 범위 설정
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.set_ylim(0, 1.2)
    
    # 타이틀 설정
    plt.title('Fear & Greed Index',
             y=1.2, fontsize=16, fontweight='bold')
    
    return fig