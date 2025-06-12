import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SearchProgressComponent } from './progress';

describe('Progress', () => {
  let component: SearchProgressComponent;
  let fixture: ComponentFixture<SearchProgressComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SearchProgressComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(SearchProgressComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
