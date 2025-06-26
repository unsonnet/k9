import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ResultsThresholdsComponent } from './thresholds';

describe('Thresholds', () => {
  let component: ResultsThresholdsComponent;
  let fixture: ComponentFixture<ResultsThresholdsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ResultsThresholdsComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(ResultsThresholdsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
